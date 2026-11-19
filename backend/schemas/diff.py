from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Tuple

from pydantic import BaseModel, Field

# Simple mapping from file extension to language name
EXTENSION_MAP: Dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".cs": "csharp",
    ".go": "go",
    ".rb": "ruby",
    ".php": "php",
    ".rs": "rust",
    ".swift": "swift",
    ".kt": "kotlin",
    ".md": "markdown",
    # add more as needed
}

def detect_language(filename: str) -> str:
    """Return a language identifier based on the file extension.
    If the extension is unknown, return ``"unknown"``.
    """
    ext = Path(filename).suffix.lower()
    return EXTENSION_MAP.get(ext, "unknown")

class FileDiffContext(BaseModel):
    """Per‑file diff summary used by the LLM for context building."""

    filename: str = Field(..., description="Path of the changed file relative to repo root")
    language: str = Field(..., description="Detected programming language (or 'unknown')")
    added_lines: int = Field(..., description="Number of lines added in this file")
    removed_lines: int = Field(..., description="Number of lines removed in this file")
    added_functions: List[str] = Field(default_factory=list, description="Names of functions added (Python only)")
    removed_functions: List[str] = Field(default_factory=list, description="Names of functions removed (Python only)")
    added_classes: List[str] = Field(default_factory=list, description="Names of classes added (Python only)")
    removed_classes: List[str] = Field(default_factory=list, description="Names of classes removed (Python only)")
    # For future language‑specific extraction you could add methods/attributes here.

class PRContext(BaseModel):
    """Aggregated diff analysis for a PR.
    This model is passed to the downstream LLM question‑generation stage.
    """

    total_files: int = Field(..., description="Number of files touched by the PR")
    total_added: int = Field(..., description="Total added lines across all files")
    total_removed: int = Field(..., description="Total removed lines across all files")
    files: List[FileDiffContext] = Field(..., description="Detailed per‑file diff information")
    # Simple heuristic concepts – extracted from identifiers (e.g., class/func names)
    important_concepts: List[str] = Field(default_factory=list, description="High‑level concepts derived from names")
    potential_edge_cases: List[str] = Field(default_factory=list, description="Possible edge‑case indicators, e.g., "
                                                    "exception handling, input validation, "
                                                    "resource cleanup, etc.")

    class Config:
        json_encoders = {"datetime": lambda v: v.isoformat()}

