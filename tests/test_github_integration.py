import asyncio
from datetime import datetime
from typing import Any, Dict
import httpx
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.github_client import GitHubClient, _parse_repo_url, GitHubError


def test_parse_repo_url_valid():
    owner, repo = _parse_repo_url("https://github.com/fastapi/fastapi")
    assert owner == "fastapi"
    assert repo == "fastapi"


def test_parse_repo_url_invalid():
    with pytest.raises(ValueError):
        _parse_repo_url("https://gitlab.com/owner/repo")


@pytest.mark.asyncio
async def test_github_client_success():
    repo_payload = {
        "description": "FastAPI framework",
        "homepage": None,
        "private": False,
        "default_branch": "master",
    }
    pr_payload = {
        "number": 1,
        "title": "Initial commit",
        "body": "Add initial files",
        "state": "open",
        "merged": False,
        "merged_at": None,
        "user": {"login": "tiangolo"},
        "created_at": "2020-12-04T20:46:15Z",
        "updated_at": "2020-12-04T20:46:15Z",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/repos/fastapi/fastapi":
            return httpx.Response(200, json=repo_payload)
        elif path == "/repos/fastapi/fastapi/pulls/1":
            return httpx.Response(200, json=pr_payload)
        elif path in [
            "/repos/fastapi/fastapi/pulls/1/files",
            "/repos/fastapi/fastapi/pulls/1/commits",
            "/repos/fastapi/fastapi/pulls/1/comments",
        ]:
            return httpx.Response(200, json=[])
        return httpx.Response(404, json={"message": "Not found"})

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="https://api.github.com")

    gh = GitHubClient()
    gh.client = client
    result = await gh.fetch_full_pr("https://github.com/fastapi/fastapi", 1)
    assert result.repository.owner == "fastapi"
    assert result.repository.name == "fastapi"
    assert result.pull_request.title == "Initial commit"
    assert result.pull_request.author == "tiangolo"
    assert isinstance(result.pull_request.created_at, datetime)
    await gh.close()


def test_fastapi_health_endpoint():
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
