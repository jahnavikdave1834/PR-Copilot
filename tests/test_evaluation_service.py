import pytest
from backend.schemas.question import Question
from backend.services.evaluation_service import evaluate_answer


def test_evaluate_answer_full_credit():
    question = Question(
        text="Explain how the helper function handles errors.",
        category="edge_case",
        difficulty="medium",
        evidence=[],
        expected_answer_concepts=["try-except", "ValueError"],
        evaluation_criteria=[],
    )
    answer = "The function wraps execution in a try-except block and raises a ValueError if invalid input is given."
    result = evaluate_answer(question, answer)

    assert result.max_score == 20
    assert result.score == 20
    assert len(result.missing_concepts) == 0
    assert "try-except" in result.correct_concepts
    assert "ValueError" in result.correct_concepts
    assert result.uncertainty is False


def test_evaluate_answer_missing_concepts():
    question = Question(
        text="Explain how the helper function handles errors.",
        category="edge_case",
        difficulty="hard",
        evidence=[],
        expected_answer_concepts=["try-except", "ValueError", "exception chaining"],
        evaluation_criteria=[],
    )
    answer = "It uses a try-except block to catch bad stuff."
    result = evaluate_answer(question, answer)

    assert result.max_score == 30
    assert result.score < 30
    assert "valueerror" in [c.lower() for c in result.missing_concepts]
    assert "exception chaining" in result.missing_concepts
    assert result.follow_up_question is not None


def test_evaluate_answer_misconception_penalty():
    question = Question(
        text="Why was this implemented this way?",
        category="reasoning",
        difficulty="easy",
        evidence=[],
        expected_answer_concepts=["performance"],
        evaluation_criteria=[],
    )
    answer = "It was just a quick and dirty hack for performance TODO fixme."
    result = evaluate_answer(question, answer)

    assert result.score < 10
    assert len(result.misconceptions) > 0
