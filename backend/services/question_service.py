"""Service to generate AI‑driven technical questions from a PR context.
It uses the Groq LLM client (``backend.core.llm_client.get_groq_client``) to
produce a list of ``Question`` objects defined in ``backend.schemas.question``.
If the LLM call fails, a ``QuestionGenerationError`` is raised.
"""

from __future__ import annotations

import json
import re
from typing import List

from loguru import logger

from ..core.llm_client import get_groq_client, GroqClient
from ..schemas.diff import PRContext
from ..schemas.question import Question, QuestionsResponse


class QuestionGenerationError(RuntimeError):
    """Raised when the LLM fails to produce a valid question list."""


def _extract_json_array(text: str) -> List[dict]:
    """Robustly parse JSON array from raw model text, stripping markdown if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "questions" in data and isinstance(data["questions"], list):
            return data["questions"]
    except Exception:
        pass

    match = re.search(r"\[\s*\{.*\}\s*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    raise ValueError(f"Could not extract JSON questions array from model output: {text[:200]}")


def _generate_ast_fallback_questions(context: PRContext) -> List[dict]:
    """Deterministically generate grounded questions directly from AST diff context
    when Groq LLM API is unavailable or unconfigured.
    """
    files = context.files or []
    primary_file = files[0].filename if files else "source/main.py"
    all_funcs = [fn for f in files for fn in (getattr(f, "added_functions", []) or [])]
    all_classes = [cl for f in files for cl in (getattr(f, "added_classes", []) or [])]
    concepts = context.important_concepts or ["endpoint", "validation", "parameter"]

    func_str = ", ".join(all_funcs[:3]) if all_funcs else "the modified endpoints/routines"
    class_str = ", ".join(all_classes[:2]) if all_classes else "the core structure"

    return [
        {
            "text": f"Explain the architectural purpose of the changes in {primary_file}. What specific requirements or functionality do these diffs address?",
            "category": "comprehension",
            "difficulty": "easy",
            "evidence": [{"filename": primary_file, "start_line": 1, "end_line": 50}],
            "expected_answer_concepts": concepts[:3] if concepts else ["functionality", "logic", "parameters"],
            "evaluation_criteria": ["Clarity of purpose", "Accurate mapping to PR goals"],
        },
        {
            "text": f"Why was the implementation in {func_str} structured in this manner? How does it integrate with existing module dependencies?",
            "category": "reasoning",
            "difficulty": "medium",
            "evidence": [{"filename": primary_file, "start_line": None, "end_line": None}],
            "expected_answer_concepts": ["architecture", "dependencies", "integration"],
            "evaluation_criteria": ["Technical rationale", "System integration awareness"],
        },
        {
            "text": f"What potential edge cases or failure modes (e.g. boundary validation, exception handling) exist in these changes, and how does the code mitigate them?",
            "category": "edge_case",
            "difficulty": "hard",
            "evidence": [{"filename": primary_file, "start_line": None, "end_line": None}],
            "expected_answer_concepts": ["exception", "validation", "boundary", "error"],
            "evaluation_criteria": ["Edge-case identification", "Robustness of error handling"],
        },
        {
            "text": f"What alternative design approaches or performance trade-offs were considered when authoring {class_str} or modifying existing logic?",
            "category": "decision",
            "difficulty": "medium",
            "evidence": [{"filename": primary_file, "start_line": None, "end_line": None}],
            "expected_answer_concepts": ["trade-off", "performance", "maintainability"],
            "evaluation_criteria": ["Trade-off analysis", "Maintainability justification"],
        },
        {
            "text": f"How should these code changes be validated and tested? What assertions or edge conditions must be covered in unit/integration test suites?",
            "category": "debugging",
            "difficulty": "easy",
            "evidence": [{"filename": primary_file, "start_line": None, "end_line": None}],
            "expected_answer_concepts": ["test", "assertion", "regression", "coverage"],
            "evaluation_criteria": ["Test coverage completeness", "Regression prevention"],
        },
    ]


async def _call_groq(context: PRContext) -> List[dict]:
    """Invoke Groq with a system prompt and the serialized PR context."""
    client: GroqClient = get_groq_client()
    system_prompt = (
        "You are an AI tutor generating technical evaluation questions for an intern who authored or reviewed a PR. "
        "Given the PR context JSON, generate between 5 and 8 questions. "
        "Questions must cover: comprehension, reasoning, decision, edge_case, debugging, and concept. "
        "Respond ONLY with a JSON array of objects conforming to: "
        '{"text": str, "category": str, "difficulty": "easy"|"medium"|"hard", '
        '"evidence": [{"filename": str, "start_line": int|null, "end_line": int|null}], '
        '"expected_answer_concepts": [str], "evaluation_criteria": [str]}'
    )
    context_json = context.model_dump_json() if hasattr(context, "model_dump_json") else context.json()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"PR Context:\n{context_json}"},
    ]
    try:
        response = await client.chat(messages)
        content = response["choices"][0]["message"]["content"]
        return _extract_json_array(content)
    except Exception as exc:
        logger.error("Failed to generate or parse Groq questions: {}", exc)
        raise QuestionGenerationError(str(exc)) from exc
    finally:
        await client.close()


async def generate_questions(pr_context: PRContext) -> QuestionsResponse:
    """Public entry point used by API routes to generate questions."""
    raw_questions = None
    try:
        raw_questions = await _call_groq(pr_context)
    except Exception as exc:
        logger.warning("Groq question generation unavailable ({}), using AST-grounded questions", exc)
        raw_questions = _generate_ast_fallback_questions(pr_context)

    questions: List[Question] = []
    for q_dict in raw_questions:
        try:
            if hasattr(Question, "model_validate"):
                q = Question.model_validate(q_dict)
            else:
                q = Question.parse_obj(q_dict)
            questions.append(q)
        except Exception as exc:
            logger.warning("Skipping invalid question schema item: {}", exc)

    if not questions:
        raw_fallback = _generate_ast_fallback_questions(pr_context)
        questions = [Question.model_validate(item) for item in raw_fallback]

    return questions
