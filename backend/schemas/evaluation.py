"""Schema definitions for answer evaluation results.
These models are used by the evaluation service and the report generator.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    """Result of scoring a single answer."""
    score: int = Field(..., ge=0, description="Points earned for the answer")
    max_score: int = Field(..., gt=0, description="Maximum possible points for the question")
    feedback: str = Field(..., description="Human‑readable feedback for the intern")
    correct_concepts: List[str] = Field(default_factory=list, description="Concepts correctly addressed")
    missing_concepts: List[str] = Field(default_factory=list, description="Concepts that were not addressed")
    misconceptions: List[str] = Field(default_factory=list, description="Incorrect ideas detected in the answer")
    expected_answer_concepts: List[str] = Field(default_factory=list, description="Expected concepts for question")
    pr_evidence: Optional[List[Dict[str, Any]]] = Field(default=None, description="PR evidence references")
    follow_up_question: Optional[str] = Field(None, description="Optional mentor follow‑up question")
    uncertainty: bool = Field(False, description="True if the evaluator is unsure about the answer")


EvaluationResults = List[EvaluationResult]
