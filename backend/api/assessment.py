"""FastAPI router for assessment workflow.
Endpoints:
- POST /api/assessment/generate   → create assessment, fetch PR, diff, generate questions
- POST /api/assessment/submit     → submit answers, evaluate, generate report
- GET  /api/assessment/{id}      → retrieve assessment details
"""

from __future__ import annotations

import json
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Body
from loguru import logger

from ..services.github_service import fetch_pr_data
from ..core.diff_analyzer import analyze_pr
from ..services.question_service import generate_questions, generate_ast_fallback_questions, QuestionGenerationError
from ..services.evaluation_service import evaluate_answer, EvaluationError
from ..services.report_service import generate_report
from ..db.database import get_db, init_db, Intern, Assessment, QuestionRecord, AnswerRecord, EvaluationRecord, ReportRecord
from ..schemas.github import PullRequestFullResponse
from ..schemas.question import Question, FileReference
from ..schemas.evaluation import EvaluationResult

router = APIRouter()

# Ensure DB tables exist
init_db()


@router.post("/assessment/generate", summary="Create assessment and generate questions")
async def generate_assessment(
    repo_url: str = Body(..., embed=True, description="GitHub repository HTTPS URL"),
    pr_number: int = Body(..., embed=True, ge=1, description="Pull request number"),
    intern_id: str = Body(..., embed=True, description="Intern identifier (e.g., email or username)"),
    pr_data: Optional[dict] = Body(None, embed=True, description="Optional pre-fetched PR preview metadata"),
):
    """Fetch PR, analyse diff, generate technical questions and persist a new assessment session."""
    if pr_data:
        try:
            if hasattr(PullRequestFullResponse, "model_validate"):
                pr = PullRequestFullResponse.model_validate(pr_data)
            else:
                pr = PullRequestFullResponse.parse_obj(pr_data)
        except Exception:
            pr = await fetch_pr_data(repo_url, pr_number)
    else:
        try:
            pr = await fetch_pr_data(repo_url, pr_number)
        except Exception as exc:
            logger.error("GitHub fetch failed: {}", exc)
            raise HTTPException(status_code=502, detail=f"Failed to fetch PR: {exc}") from exc

    pr_context = analyze_pr(pr)

    try:
        questions: List[Question] = await generate_questions(pr_context)
    except Exception as exc:
        logger.warning("Groq question generation unavailable ({}), using AST-grounded questions", exc)
        questions = generate_ast_fallback_questions(pr_context)

    with get_db() as db:
        intern = db.query(Intern).filter_by(identifier=intern_id).first()
        if not intern:
            intern = Intern(identifier=intern_id)
            db.add(intern)
            db.flush()

        pr_meta_json = pr.model_dump_json() if hasattr(pr, "model_dump_json") else pr.json()
        diff_ctx_json = pr_context.model_dump_json() if hasattr(pr_context, "model_dump_json") else pr_context.json()

        assessment = Assessment(
            intern_id=intern.id,
            repo_url=repo_url,
            pr_number=pr_number,
            pr_metadata=pr_meta_json,
            diff_context=diff_ctx_json,
        )
        db.add(assessment)
        db.flush()

        saved_questions = []
        for q in questions:
            ev_json = json.dumps([e.dict() if hasattr(e, "dict") else dict(e) for e in q.evidence]) if q.evidence else None
            exp_concepts_json = json.dumps(q.expected_answer_concepts) if q.expected_answer_concepts else None

            qrec = QuestionRecord(
                assessment_id=assessment.id,
                text=q.text,
                category=q.category,
                difficulty=q.difficulty,
                evidence=ev_json,
                expected_concepts=exp_concepts_json,
            )
            db.add(qrec)
            db.flush()

            saved_questions.append({
                "id": qrec.id,
                "text": q.text,
                "category": q.category,
                "difficulty": q.difficulty,
                "evidence": [e.dict() if hasattr(e, "dict") else dict(e) for e in q.evidence],
                "expected_answer_concepts": q.expected_answer_concepts,
                "evaluation_criteria": q.evaluation_criteria,
            })

        saved_assessment_id = assessment.id
        db.commit()

    return {
        "assessment_id": saved_assessment_id,
        "repo_url": repo_url,
        "pr_number": pr_number,
        "intern_id": intern_id,
        "questions": saved_questions,
    }


@router.post("/assessment/submit", summary="Submit answers, evaluate, and generate mentor report")
async def submit_assessment(
    assessment_id: int = Body(..., embed=True),
    answers: Dict[str, str] = Body(..., embed=True, description="Map of question_id (as str or int) to answer text"),
):
    """Store submitted answers, perform evaluation for each, generate a structured report and persist."""
    with get_db() as db:
        assessment = db.query(Assessment).filter_by(id=assessment_id).first()
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        eval_results: List[EvaluationResult] = []

        for qid_raw, ans_text in answers.items():
            try:
                qid = int(qid_raw)
            except ValueError:
                continue

            qrec = db.query(QuestionRecord).filter_by(id=qid, assessment_id=assessment_id).first()
            if not qrec:
                continue

            answer_rec = db.query(AnswerRecord).filter_by(question_id=qid).first()
            if not answer_rec:
                answer_rec = AnswerRecord(question_id=qid, answer_text=ans_text)
                db.add(answer_rec)
                db.flush()
            else:
                answer_rec.answer_text = ans_text
                db.flush()

            expected_concepts = []
            if qrec.expected_concepts:
                try:
                    expected_concepts = json.loads(qrec.expected_concepts)
                except Exception:
                    expected_concepts = [c.strip() for c in qrec.expected_concepts.split(",") if c.strip()]

            q_model = Question(
                text=qrec.text,
                category=qrec.category,
                difficulty=qrec.difficulty,
                evidence=[],
                expected_answer_concepts=expected_concepts,
                evaluation_criteria=[],
            )

            eval_res: EvaluationResult = evaluate_answer(q_model, ans_text)

            existing_eval = db.query(EvaluationRecord).filter_by(answer_id=answer_rec.id).first()
            if not existing_eval:
                existing_eval = EvaluationRecord(
                    answer_id=answer_rec.id,
                    score=eval_res.score,
                    max_score=eval_res.max_score,
                    feedback=eval_res.feedback,
                    missing_concepts=",".join(eval_res.missing_concepts) if eval_res.missing_concepts else None,
                    misconceptions=",".join(eval_res.misconceptions) if eval_res.misconceptions else None,
                    follow_up_question=eval_res.follow_up_question,
                    uncertainty=eval_res.uncertainty,
                )
                db.add(existing_eval)
            else:
                existing_eval.score = eval_res.score
                existing_eval.max_score = eval_res.max_score
                existing_eval.feedback = eval_res.feedback
                existing_eval.missing_concepts = ",".join(eval_res.missing_concepts) if eval_res.missing_concepts else None
                existing_eval.misconceptions = ",".join(eval_res.misconceptions) if eval_res.misconceptions else None
                existing_eval.follow_up_question = eval_res.follow_up_question
                existing_eval.uncertainty = eval_res.uncertainty

            eval_results.append(eval_res)

        db.commit()

        if not eval_results:
            raise HTTPException(status_code=400, detail="No matching answers found to evaluate")

        report_content = generate_report(assessment_id, eval_results)
        report_rec = db.query(ReportRecord).filter_by(assessment_id=assessment_id).first()
        if not report_rec:
            report_rec = ReportRecord(assessment_id=assessment_id, content=report_content)
            db.add(report_rec)
        else:
            report_rec.content = report_content
        db.flush()
        saved_report_id = report_rec.id
        db.commit()

        return {
            "report_id": saved_report_id,
            "assessment_id": assessment_id,
            "report": json.loads(report_content),
        }


@router.get("/assessment/{assessment_id}", summary="Retrieve assessment details")
async def get_assessment(assessment_id: int):
    """Retrieve an assessment by ID with questions, submitted answers, and evaluations if any."""
    with get_db() as db:
        assessment = db.query(Assessment).filter_by(id=assessment_id).first()
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        q_list = []
        for q in assessment.questions:
            evidence_list = []
            if q.evidence:
                try:
                    evidence_list = json.loads(q.evidence)
                except Exception:
                    pass

            ans_data = None
            eval_data = None
            if q.answer:
                ans_data = {
                    "id": q.answer.id,
                    "answer_text": q.answer.answer_text,
                    "submitted_at": q.answer.submitted_at.isoformat() if q.answer.submitted_at else None,
                }
                if q.answer.evaluation:
                    eval_data = {
                        "id": q.answer.evaluation.id,
                        "score": q.answer.evaluation.score,
                        "max_score": q.answer.evaluation.max_score,
                        "feedback": q.answer.evaluation.feedback,
                        "follow_up_question": q.answer.evaluation.follow_up_question,
                        "uncertainty": q.answer.evaluation.uncertainty,
                    }

            q_list.append({
                "id": q.id,
                "text": q.text,
                "category": q.category,
                "difficulty": q.difficulty,
                "evidence": evidence_list,
                "answer": ans_data,
                "evaluation": eval_data,
            })

        return {
            "id": assessment.id,
            "intern_id": assessment.intern.identifier if assessment.intern else str(assessment.intern_id),
            "repo_url": assessment.repo_url,
            "pr_number": assessment.pr_number,
            "created_at": assessment.created_at.isoformat() if assessment.created_at else None,
            "questions": q_list,
        }


@router.get("/assessments", summary="List all assessments with summary stats")
async def list_assessments():
    """Retrieve all assessments ordered by creation date desc for history and mentor dashboards."""
    with get_db() as db:
        assessments = db.query(Assessment).order_by(Assessment.created_at.desc()).all()
        results = []
        for a in assessments:
            q_count = len(a.questions)
            submitted_count = sum(1 for q in a.questions if q.answer is not None)
            total_score = sum(q.answer.evaluation.score for q in a.questions if q.answer and q.answer.evaluation)
            max_score = sum(q.answer.evaluation.max_score for q in a.questions if q.answer and q.answer.evaluation)
            pct = round((total_score / max_score) * 100, 1) if max_score > 0 else None

            results.append({
                "id": a.id,
                "intern_id": a.intern.identifier if a.intern else str(a.intern_id),
                "repo_url": a.repo_url,
                "pr_number": a.pr_number,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "question_count": q_count,
                "submitted_count": submitted_count,
                "is_completed": submitted_count >= q_count and q_count > 0,
                "score_percentage": pct,
                "total_score": total_score,
                "max_score": max_score,
                "has_report": a.report is not None,
            })
        return results
