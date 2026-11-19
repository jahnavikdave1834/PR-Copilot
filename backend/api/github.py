from fastapi import APIRouter, HTTPException, Body
from loguru import logger

from ..services.github_service import fetch_pr_data
from ..schemas.github import PullRequestFullResponse
from ..core.github_client import GitHubError

router = APIRouter()

@router.post(
    "/github/fetch-pr",
    response_model=PullRequestFullResponse,
    summary="Fetch full PR information from GitHub",
)
async def fetch_pr(
    repo_url: str = Body(..., embed=True, description="Full HTTPS URL of the GitHub repository"),
    pr_number: int = Body(..., embed=True, ge=1, description="Pull request number"),
) -> PullRequestFullResponse:
    """Validate inputs, call the internal service and return a structured response.
    Errors from the GitHub API are translated into ``HTTPException`` with appropriate
    status codes and messages.
    """
    try:
        return await fetch_pr_data(repo_url, pr_number)
    except ValueError as ve:
        logger.error("Invalid repository URL: {}", ve)
        raise HTTPException(status_code=422, detail=str(ve)) from ve
    except GitHubError as ghe:
        # Map common status codes to FastAPI equivalents
        status_map = {404: 404, 401: 401, 403: 429}
        http_status = status_map.get(ghe.status_code, 502)
        if ghe.status_code == 404:
            detail_msg = f"Pull request #{pr_number} was not found on GitHub for repository '{repo_url}'. Please check that the repository and PR number exist and are publicly accessible."
        else:
            detail_msg = ghe.detail
        logger.error("GitHub API error {}: {}", ghe.status_code, detail_msg)
        raise HTTPException(status_code=http_status, detail=detail_msg) from ghe

