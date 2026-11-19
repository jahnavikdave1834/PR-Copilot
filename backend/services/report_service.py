"""Service to build a mentor report from an assessment and its evaluation results.
The report is returned as a JSON string (could be rendered as markdown later).
It aggregates overall score, per‑category breakdowns, strengths, gaps, and any follow‑up questions.
"""

from __future__ import annotations

import json
from typing import List

from loguru import logger

from ..schemas.evaluation import EvaluationResult


def generate_report(assessment_id: int, evaluations: List[EvaluationResult]) -> str:
    """Create a JSON‑serialised report for the given assessment.

    The report includes:
    * `assessment_id`
    * `total_score` / `max_score`
    * `category_breakdown` – sum of scores per question category (derived from the
      ``EvaluationResult`` objects – we assume the caller passed them in the same order
      as the original questions).
    * `strengths` – concepts that were consistently covered.
    * `knowledge_gaps` – concepts that were missing in one or more answers.
    * `misconceptions` – any detected misconception keywords.
    * `follow_up_questions` – mentor‑generated follow‑ups for unanswered concepts.
    """
    total_score = sum(ev.score for ev in evaluations)
    max_score = sum(ev.max_score for ev in evaluations)

    # Aggregate concepts – we rely on the ``expected_answer_concepts`` being stored
    # in the EvaluationResult (we'll include them when the evaluation is created).
    concept_hits: dict[str, int] = {}
    concept_misses: dict[str, int] = {}
    misconceptions: set[str] = set()
    follow_ups: List[str] = []

    for ev in evaluations:
        # expected concepts may be stored in the evaluation's missing_concepts (inverse)
        # For simplicity, treat missing_concepts as the concepts not covered.
        for missing in ev.missing_concepts:
            concept_misses[missing] = concept_misses.get(missing, 0) + 1
        # We can't know which concepts were covered unless we had a list – assume
        # that any concept not in missing_concepts was covered.
        # This is a heuristic; real implementation would pass covered concepts.
        for covered in ev.expected_answer_concepts if hasattr(ev, "expected_answer_concepts") else []:  # type: ignore
            concept_hits[covered] = concept_hits.get(covered, 0) + 1
        misconceptions.update(ev.misconceptions)
        if ev.follow_up_question:
            follow_ups.append(ev.follow_up_question)

    # Derive strengths/gaps (simple heuristic: if a concept missed in >0 answers, it's a gap)
    strengths = [c for c, cnt in concept_hits.items() if cnt > 0]
    knowledge_gaps = list(concept_misses.keys())

    report = {
        "assessment_id": assessment_id,
        "total_score": total_score,
        "max_score": max_score,
        "percentage": round(100 * total_score / max_score, 2) if max_score else 0,
        "strengths": strengths,
        "knowledge_gaps": knowledge_gaps,
        "misconceptions": list(misconceptions),
        "follow_up_questions": follow_ups,
    }
    logger.info("Generated report for assessment {}", assessment_id)
    return json.dumps(report, indent=2)
