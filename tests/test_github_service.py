import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from backend.schemas.github import (
    PullRequestFullResponse,
    RepoInfo,
    PullRequestInfo,
    FileChange,
)
from backend.core.github_client import GitHubError
from backend.services.github_service import fetch_pr_data, _normalize_repo_url


def make_dummy_pr():
    return PullRequestFullResponse(
        repository=RepoInfo(
            owner="user",
            name="repo",
            description="Test repo",
            homepage=None,
            private=False,
            default_branch="main",
        ),
        pull_request=PullRequestInfo(
            number=1,
            title="Test PR",
            body="Test body",
            state="open",
            merged=False,
            author="tester",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            merged_at=None,
        ),
        files=[],
        commits=[],
        reviews=[],
    )


def test_normalize_repo_url():
    assert _normalize_repo_url("https://github.com/user/repo.git") == "https://github.com/user/repo"
    assert _normalize_repo_url("http://github.com/user/repo/") == "https://github.com/user/repo"
    with pytest.raises(ValueError):
        _normalize_repo_url("git@github.com:user/repo.git")


def test_fetch_pr_success():
    async def _run():
        dummy = make_dummy_pr()
        mock_client = AsyncMock()
        mock_client.fetch_full_pr.return_value = dummy
        mock_client.close = AsyncMock()
        with patch("backend.services.github_service.get_github_client", return_value=mock_client):
            result = await fetch_pr_data("https://github.com/user/repo", 1)
            assert result == dummy
            mock_client.fetch_full_pr.assert_awaited_once_with("https://github.com/user/repo", 1)

    asyncio.run(_run())


def test_fetch_pr_error_propagates():
    async def _run():
        mock_client = AsyncMock()
        mock_client.fetch_full_pr.side_effect = GitHubError(404, "Not found")
        mock_client.close = AsyncMock()
        with patch("backend.services.github_service.get_github_client", return_value=mock_client):
            with pytest.raises(GitHubError) as exc:
                await fetch_pr_data("https://github.com/user/repo", 999)
            assert exc.value.status_code == 404

    asyncio.run(_run())
