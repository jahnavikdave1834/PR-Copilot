import json
import pytest
from unittest.mock import AsyncMock, patch

from backend.schemas.diff import PRContext, FileDiffContext
from backend.schemas.question import Question
from backend.services.question_service import generate_questions, QuestionGenerationError


def test_question_schema_validation():
    q = Question(
        text="Why was the model updated?",
        category="reasoning",
        difficulty="medium",
        evidence=[{"filename": "model.py", "start_line": 10, "end_line": 20}],
        expected_answer_concepts=["cross-entropy", "loss"],
        evaluation_criteria=["Mentions loss function update"],
    )
    assert q.text == "Why was the model updated?"
    assert q.category == "reasoning"
    assert q.difficulty == "medium"
    assert len(q.evidence) == 1
    assert q.evidence[0].filename == "model.py"


def test_generate_questions_success():
    mock_questions_raw = [
        {
            "text": "What is the role of new_helper?",
            "category": "comprehension",
            "difficulty": "easy",
            "evidence": [{"filename": "utils.py", "start_line": 1, "end_line": 6}],
            "expected_answer_concepts": ["helper function", "multiplication"],
            "evaluation_criteria": ["Identifies function purpose"],
        },
        {
            "text": "How does error handling work in this PR?",
            "category": "edge_case",
            "difficulty": "medium",
            "evidence": [{"filename": "utils.py", "start_line": 4, "end_line": 6}],
            "expected_answer_concepts": ["try-except", "ValueError"],
            "evaluation_criteria": ["Explains exception raising"],
        },
    ]

    mock_llm_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(mock_questions_raw),
                }
            }
        ]
    }

    mock_groq_client = AsyncMock()
    mock_groq_client.chat.return_value = mock_llm_response
    mock_groq_client.close = AsyncMock()

    ctx = PRContext(
        total_files=1,
        total_added=6,
        total_removed=0,
        files=[
            FileDiffContext(
                filename="utils.py",
                language="python",
                added_lines=6,
                removed_lines=0,
                added_functions=["new_helper"],
                removed_functions=[],
                added_classes=[],
                removed_classes=[],
            )
        ],
        important_concepts=["new_helper"],
        potential_edge_cases=["try", "except"],
    )

    import asyncio
    async def _run():
        with patch("backend.services.question_service.get_groq_client", return_value=mock_groq_client):
            questions = await generate_questions(ctx)
            assert len(questions) == 2
            assert questions[0].text == "What is the role of new_helper?"
            assert questions[0].category == "comprehension"
            assert questions[1].difficulty == "medium"

    asyncio.run(_run())


def test_generate_questions_malformed_json_failure():
    mock_llm_response = {
        "choices": [{"message": {"content": "Not valid JSON output from LLM"}}]
    }
    mock_groq_client = AsyncMock()
    mock_groq_client.chat.return_value = mock_llm_response
    mock_groq_client.close = AsyncMock()

    ctx = PRContext(
        total_files=1,
        total_added=1,
        total_removed=0,
        files=[],
        important_concepts=[],
        potential_edge_cases=[],
    )

    import asyncio
    async def _run():
        with patch("backend.services.question_service.get_groq_client", return_value=mock_groq_client):
            with pytest.raises(QuestionGenerationError):
                await generate_questions(ctx)

    asyncio.run(_run())
