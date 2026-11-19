"""Async GitHub client for PR Understanding Copilot.
Handles authentication, pagination, rate‑limit handling and error mapping.
All network I/O is performed with ``httpx.AsyncClient``.
"""

from __future__ import annotations
from datetime import datetime

import asyncio
import time
from typing import List, Tuple
from urllib.parse import urlparse

import httpx
from loguru import logger

from ..config.settings import settings
from ..schemas.github import (
    RepoInfo,
    PullRequestInfo,
    FileChange,
    CommitInfo,
    ReviewComment,
    PullRequestFullResponse,
)


class GitHubError(RuntimeError):
    """Raised for any non‑successful interaction with the GitHub API.
    Contains the HTTP status code and a short message.
    """

    def __init__(self, status_code: int, detail: str):
        super().__init__(f"GitHub API error {status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail


def _parse_repo_url(url: str) -> Tuple[str, str]:
    """Validate a GitHub HTTPS URL and return ``(owner, repo)``.

    Accepted formats:
        https://github.com/<owner>/<repo>
        https://github.com/<owner>/<repo>.git
    Anything else raises ``ValueError``.
    """
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != "github.com":
        raise ValueError("Invalid GitHub repository URL – must be https://github.com/<owner>/<repo>")
    # path may start with a slash
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2:
        raise ValueError("Repository URL must contain both owner and repository name")
    owner, repo = parts[0], parts[1]
    if repo.endswith('.git'):
        repo = repo[:-4]
    return owner, repo


class GitHubClient:
    """Thin wrapper around the public GitHub REST API.

    The client is deliberately lightweight – it does **not** implement the full
    GitHub API surface, only the endpoints required for the Copilot pipeline.
    All public methods are ``async`` and can be awaited directly or used with
    ``asyncio.run`` in scripts.
    """

    BASE_URL = "https://api.github.com"
    TIMEOUT = 10.0  # seconds for each request
    PER_PAGE = 100  # max page size supported by the API

    def __init__(self, token: str | None = None):
        self.token = token or settings.github_token
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        self.client = httpx.AsyncClient(timeout=self.TIMEOUT, headers=self.headers)

    async def _request(self, method: str, url: str, params: dict | None = None) -> httpx.Response:
        """Send a request and handle rate‑limit / HTTP errors.
        Retries with exponential back‑off when ``X‑RateLimit-Remaining`` is 0.
        """
        attempt = 0
        while True:
            attempt += 1
            try:
                response = await self.client.request(method, url, params=params)
            except httpx.RequestError as exc:
                raise GitHubError(0, f"Network error: {exc}") from exc

            if response.status_code == 403 and "X-RateLimit-Remaining" in response.headers:
                remaining = int(response.headers.get("X-RateLimit-Remaining", "0"))
                if remaining == 0:
                    reset_ts = int(response.headers.get("X-RateLimit-Reset", "0"))
                    wait_seconds = max(reset_ts - int(time.time()), 1)
                    logger.warning("GitHub rate limit exhausted, sleeping {}s (attempt {})", wait_seconds, attempt)
                    await asyncio.sleep(wait_seconds)
                    continue  # retry after sleep
            if 200 <= response.status_code < 300:
                return response
            # For other error statuses raise a structured exception
            try:
                detail = response.json().get("message", response.text)
            except Exception:
                detail = response.text
            raise GitHubError(response.status_code, detail)

    async def get_repository(self, owner: str, repo: str) -> RepoInfo:
        url = f"{self.BASE_URL}/repos/{owner}/{repo}"
        resp = await self._request("GET", url)
        data = resp.json()
        return RepoInfo(
            owner=owner,
            name=repo,
            description=data.get("description"),
            homepage=data.get("homepage"),
            private=data.get("private", False),
            default_branch=data.get("default_branch", "main"),
        )

    async def get_pull_request(self, owner: str, repo: str, number: int) -> PullRequestInfo:
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{number}"
        resp = await self._request("GET", url)
        data = resp.json()
        state = "merged" if data.get("merged_at") else data.get("state")
        return PullRequestInfo(
            number=data["number"],
            title=data.get("title", ""),
            body=data.get("body"),
            state=state,  # type: ignore[assignment]
            merged=data.get("merged", False),
            author=data["user"]["login"],
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
            merged_at=datetime.fromisoformat(data["merged_at"].replace("Z", "+00:00")) if data.get("merged_at") else None,
        )

    async def _collect_paginated(self, endpoint: str, model_cls, **extra_params) -> List:
        """Generic paginator – follows ``Link`` header for ``rel="next"``.
        ``model_cls`` is a Pydantic model that will be instantiated for each item.
        """
        items: List = []
        params = {"per_page": self.PER_PAGE, **extra_params}
        url = f"{self.BASE_URL}{endpoint}"
        while url:
            resp = await self._request("GET", url, params=params if "?" not in url else None)
            data = resp.json()
            items.extend([model_cls(**item) for item in data])
            # Parse Link header for next page
            link = resp.headers.get("Link")
            next_url = None
            if link:
                for part in link.split(","):
                    if "rel=\"next\"" in part:
                        next_url = part[part.find("<") + 1 : part.find(">")]
                        break
            url = next_url
            # Params only needed on first request
            params = {}
        return items

    async def list_files(self, owner: str, repo: str, pr_number: int) -> List[FileChange]:
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}/files"
        return await self._collect_paginated(endpoint, FileChange)

    async def list_commits(self, owner: str, repo: str, pr_number: int) -> List[CommitInfo]:
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}/commits"
        # The raw API returns a list of commit objects; we map to our model manually
        raw = await self._collect_paginated(endpoint, lambda **kw: kw)  # type: ignore[arg-type]
        commits: List[CommitInfo] = []
        for item in raw:
            commit = item.get("commit", {})
            author = commit.get("author", {})
            commits.append(
                CommitInfo(
                    sha=item.get("sha"),
                    author_name=author.get("name"),
                    author_email=author.get("email"),
                    message=commit.get("message", ""),
                    date=datetime.fromisoformat(author.get("date", "1970-01-01T00:00:00Z").replace("Z", "+00:00")),
                )
            )
        return commits

    async def list_review_comments(self, owner: str, repo: str, pr_number: int) -> List[ReviewComment]:
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        raw = await self._collect_paginated(endpoint, lambda **kw: kw)  # type: ignore[arg-type]
        comments: List[ReviewComment] = []
        for item in raw:
            comments.append(
                ReviewComment(
                    id=item["id"],
                    body=item.get("body", ""),
                    user=item["user"]["login"],
                    created_at=datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")),
                    path=item.get("path"),
                    position=item.get("position"),
                )
            )
        return comments

    async def fetch_full_pr(self, repo_url: str, pr_number: int) -> PullRequestFullResponse:
        """High‑level helper that returns a fully populated ``PullRequestFullResponse``.
        It validates the URL, then performs parallel requests for repo info, PR meta,
        files, commits and review comments.
        """
        owner, repo = _parse_repo_url(repo_url)
        # Parallel fetches – use ``asyncio.gather``
        repo_task = self.get_repository(owner, repo)
        pr_task = self.get_pull_request(owner, repo, pr_number)
        files_task = self.list_files(owner, repo, pr_number)
        commits_task = self.list_commits(owner, repo, pr_number)
        reviews_task = self.list_review_comments(owner, repo, pr_number)
        repository, pull_request, files, commits, reviews = await asyncio.gather(
            repo_task, pr_task, files_task, commits_task, reviews_task
        )
        return PullRequestFullResponse(
            repository=repository,
            pull_request=pull_request,
            files=files,
            commits=commits,
            reviews=reviews,
        )

    async def close(self) -> None:
        await self.client.aclose()


# Convenience function for the FastAPI route (synchronous wrapper)
def get_github_client() -> GitHubClient:
    """Factory that returns a client bound to the current configuration.
    FastAPI dependencies can call this without awaiting – the returned object
    should be ``await``‑ed/closed by the caller when finished.
    """
    return GitHubClient()
