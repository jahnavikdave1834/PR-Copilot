import json
import uuid
import pytest
from backend.db.database import (
    init_db,
    get_db,
    Intern,
    Assessment,
    QuestionRecord,
    AnswerRecord,
    EvaluationRecord,
    ReportRecord,
)
from backend.schemas.evaluation import EvaluationResult
from backend.services.report_service import generate_report


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_db_persistence_and_relationships():
    with get_db() as db:
        # Create intern with unique identifier
        unique_id = f"intern_{uuid.uuid4().hex[:8]}@example.com"
        intern = Intern(identifier=unique_id)
        db.add(intern)
        db.commit()
        db.refresh(intern)
        assert intern.id is not None

        # Create assessment
        assessment = Assessment(
            intern_id=intern.id,
            repo_url="https://github.com/test/repo",
            pr_number=42,
            pr_metadata=json.dumps({"title": "Test PR"}),
            diff_context=json.dumps({"total_files": 1}),
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        assert assessment.id is not None

        # Add question
        qrec = QuestionRecord(
            assessment_id=assessment.id,
            text="What does this change do?",
            category="comprehension",
            difficulty="easy",
            expected_concepts=json.dumps(["logic", "caching"]),
        )
        db.add(qrec)
        db.commit()
        db.refresh(qrec)
        assert qrec.id is not None

        # Add answer
        ansrec = AnswerRecord(
            question_id=qrec.id,
            answer_text="It implements caching logic.",
        )
        db.add(ansrec)
        db.commit()
        db.refresh(ansrec)
        assert ansrec.id is not None

        # Add evaluation
        evalrec = EvaluationRecord(
            answer_id=ansrec.id,
            score=10,
            max_score=10,
            feedback="Excellent response.",
            missing_concepts=None,
            misconceptions=None,
            follow_up_question=None,
            uncertainty=False,
        )
        db.add(evalrec)
        db.commit()
        db.refresh(evalrec)
        assert evalrec.id is not None

        # Verify relationships
        reloaded_assessment = db.query(Assessment).filter_by(id=assessment.id).first()
        assert len(reloaded_assessment.questions) == 1
        assert reloaded_assessment.questions[0].answer is not None
        assert reloaded_assessment.questions[0].answer.evaluation is not None
        assert reloaded_assessment.questions[0].answer.evaluation.score == 10


def test_report_generation():
    evals = [
        EvaluationResult(
            score=18,
            max_score=20,
            feedback="Good",
            missing_concepts=["validation"],
            misconceptions=[],
            expected_answer_concepts=["caching", "validation"],
            follow_up_question="How is validation performed?",
            uncertainty=False,
        ),
        EvaluationResult(
            score=10,
            max_score=10,
            feedback="Perfect",
            missing_concepts=[],
            misconceptions=[],
            expected_answer_concepts=["index"],
            follow_up_question=None,
            uncertainty=False,
        ),
    ]

    report_str = generate_report(assessment_id=1, evaluations=evals)
    report_dict = json.loads(report_str)

    assert report_dict["assessment_id"] == 1
    assert report_dict["total_score"] == 28
    assert report_dict["max_score"] == 30
    assert report_dict["percentage"] == round(28 / 30 * 100, 2)
    assert "validation" in report_dict["knowledge_gaps"]
    assert len(report_dict["follow_up_questions"]) == 1
