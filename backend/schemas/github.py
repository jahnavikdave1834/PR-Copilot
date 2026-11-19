"""Pydantic models for GitHub API responses used by the Copilot backend.
These models are intentionally lightweight – they include only the fields
required by the downstream modules (question generation, diff analysis, etc.).
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class RepoInfo(BaseModel):
    """Minimal repository metadata returned by the GitHub API."""

    owner: str = Field(..., description="Repository owner (user or organization)")
    name: str = Field(..., description="Repository name")
    description: Optional[str] = Field(None, description="Short description")
    homepage: Optional[HttpUrl] = Field(None, description="Homepage URL if set")
    private: bool = Field(..., description="True if the repo is private")
    default_branch: str = Field(..., description="Default branch name (e.g., 'main' or 'master')")


class PullRequestInfo(BaseModel):
    """Core PR fields needed by the Copilot pipeline."""

    number: int = Field(..., description="Pull request number")
    title: str = Field(..., description="PR title")
    body: Optional[str] = Field(None, description="Full PR description/body")
    state: Literal["open", "closed", "merged"] = Field(..., description="Current PR state")
    merged: bool = Field(..., description="True if the PR has been merged")
    author: str = Field(..., description="Login name of the PR creator")
    created_at: datetime = Field(..., description="Timestamp when the PR was opened")
    updated_at: datetime = Field(..., description="Timestamp of the last update")
    merged_at: Optional[datetime] = Field(None, description="Timestamp when the PR was merged, if applicable")


class FileChange(BaseModel):
    """A single file change entry from the PR files API endpoint."""

    filename: str = Field(..., description="Path of the changed file relative to repo root")
    status: Literal["added", "modified", "removed", "renamed"] = Field(..., description="Change type")
    additions: int = Field(..., description="Number of added lines")
    deletions: int = Field(..., description="Number of removed lines")
    changes: int = Field(..., description="Total line changes (additions + deletions)")
    patch: Optional[str] = Field(
        None,
        description="Unified diff snippet for the file (may be omitted for binary files or large diffs)",
    )


class CommitInfo(BaseModel):
    """Basic information for each commit in a PR."""

    sha: str = Field(..., description="Commit SHA hash")
    author_name: Optional[str] = Field(None, description="Commit author name (if available)")
    author_email: Optional[str] = Field(None, description="Commit author email (if available)")
    message: str = Field(..., description="Commit message")
    date: datetime = Field(..., description="Commit timestamp")


class ReviewComment(BaseModel):
    """An individual review comment (inline or general)."""

    id: int = Field(..., description="Comment identifier")
    body: str = Field(..., description="Comment text")
    user: str = Field(..., description="Login of the commenter")
    created_at: datetime = Field(..., description="When the comment was posted")
    path: Optional[str] = Field(None, description="File path the comment refers to (if inline)")
    position: Optional[int] = Field(
        None, description="Line index in the diff the comment is attached to (if inline)"
    )


class PullRequestFullResponse(BaseModel):
    """Aggregated response that the API endpoint will return to the front‑end.
    It contains the repository info, the PR meta, the list of changed files,
    the list of commits, and the list of review comments.
    """

    repository: RepoInfo
    pull_request: PullRequestInfo
    files: List[FileChange]
    commits: List[CommitInfo]
    reviews: List[ReviewComment]

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

