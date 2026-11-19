"""Service layer for GitHub integration.

The router now delegates to this module so that business logic (validation,
URL normalisation, client handling) stays separate from FastAPI request/response
concerns.
"""

import re
from urllib.parse import urlparse

from ..core.github_client import GitHubClient, get_github_client, GitHubError
from ..schemas.github import PullRequestFullResponse


def _normalize_repo_url(url: str) -> str:
    """Return a canonical ``https://github.com/<owner>/<repo>`` URL.

    Accepts URLs with or without a trailing ``.git`` and with any scheme
    (http, https). Raises ``ValueError`` for malformed inputs.
    """
    if not url:
        raise ValueError("Repository URL cannot be empty")
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Repository URL must start with http:// or https://")
    # Remove possible .git suffix and any trailing slash
    path = parsed.path.rstrip("/")
    if path.endswith('.git'):
        path = path[:-4]
    # Ensure we have owner/repo
    path = path.lstrip('/')
    if '/' not in path:
        raise ValueError("Repository URL must contain owner and repository name")
    return f"https://github.com/{path}"


async def fetch_pr_data(repo_url: str, pr_number: int) -> PullRequestFullResponse:
    """Validate inputs, invoke the ``GitHubClient`` and return the full PR model.

    The function closes the client after the request to free resources.
    """
    normalized = _normalize_repo_url(repo_url)
    client: GitHubClient = get_github_client()
    try:
        return await client.fetch_full_pr(normalized, pr_number)
    except GitHubError:
        # Propagate so the API layer can translate to HTTPException
        raise
    finally:
        await client.close()

