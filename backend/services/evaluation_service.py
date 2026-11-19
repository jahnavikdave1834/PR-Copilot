"""Service to evaluate an intern's answer against a generated question.
The evaluation logic is simple, transparent and deterministic so unit tests can verify it.
It returns an ``EvaluationResult`` (defined in ``backend.schemas.evaluation``).
"""

from __future__ import annotations

from typing import List
from loguru import logger

from ..schemas.question import Question
from ..schemas.evaluation import EvaluationResult


class EvaluationError(RuntimeError):
    """Raised when the evaluation process cannot be performed."""


def evaluate_answer(question: Question, answer_text: str) -> EvaluationResult:
    """Score ``answer_text`` against ``question`` using a transparent rubric."""
    difficulty_to_max = {"easy": 10, "medium": 20, "hard": 30}
    max_score = difficulty_to_max.get(question.difficulty, 10)
    score = max_score
    missing: list[str] = []
    correct: list[str] = []
    misconceptions: list[str] = []

    lower_answer = answer_text.lower()
    
    # Check expected concepts
    for concept in question.expected_answer_concepts:
        if concept.lower() in lower_answer:
            correct.append(concept)
        else:
            missing.append(concept)
            score -= 2

    # Check for known misconception indicators or bad practices
    for bad in ["todo", "fixme", "hack", "quick and dirty"]:
        if bad in lower_answer:
            misconceptions.append(bad)
            score -= 3

    # Score clamping
    score = max(0, min(score, max_score))

    feedback_parts = []
    if correct:
        feedback_parts.append(f"Well addressed: {', '.join(correct)}.")
    if missing:
        feedback_parts.append(f"Missing key concepts: {', '.join(missing)}.")
    if misconceptions:
        feedback_parts.append(f"Potential concerns/misconceptions: {', '.join(misconceptions)}.")
    if not feedback_parts:
        feedback_parts.append("Comprehensive answer covering the expected technical concepts.")
    feedback = " ".join(feedback_parts)

    follow_up = None
    if missing:
        follow_up = f"Can you elaborate on how {missing[0]} is handled here?"

    uncertainty = score < (0.4 * max_score)

    evidence_dicts = [ev.dict() if hasattr(ev, "dict") else dict(ev) for ev in question.evidence] if question.evidence else []

    return EvaluationResult(
        score=score,
        max_score=max_score,
        feedback=feedback,
        correct_concepts=correct,
        missing_concepts=missing,
        misconceptions=misconceptions,
        expected_answer_concepts=question.expected_answer_concepts,
        pr_evidence=evidence_dicts,
        follow_up_question=follow_up,
        uncertainty=uncertainty,
    )
