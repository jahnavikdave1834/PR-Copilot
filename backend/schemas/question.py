"""Schema definitions for AI‑generated questions.
These models are used by the ``question_service`` and are validated with Pydantic.
"""

from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field

class FileReference(BaseModel):
    """Reference to a file and optionally line numbers in the PR diff.
    This allows a question to point back to the exact code snippet it concerns.
    """
    filename: str = Field(..., description="Path of the file relative to the repository root")
    # Optional line range (1‑based). If omitted the whole file is implied.
    start_line: int | None = Field(None, ge=1, description="First line of the referenced snippet")
    end_line: int | None = Field(None, ge=1, description="Last line of the referenced snippet")

class Question(BaseModel):
    """A single AI‑generated technical question.
    The ``category`` and ``difficulty`` fields are constrained to a short list of
    accepted values so downstream code can rely on them.
    """
    text: str = Field(..., description="The question wording")
    category: Literal[
        "comprehension",
        "reasoning",
        "decision",
        "edge_case",
        "debugging",
        "concept",
    ] = Field(..., description="High‑level category of the question")
    difficulty: Literal["easy", "medium", "hard"] = Field(..., description="Estimated difficulty")
    evidence: List[FileReference] = Field(default_factory=list, description="Code locations that motivated the question")
    expected_answer_concepts: List[str] = Field(default_factory=list, description="Key concepts an answer should mention")
    evaluation_criteria: List[str] = Field(default_factory=list, description="How the answer will be scored")

# Export a list type for convenience when used as a response model
QuestionsResponse = List[Question]
