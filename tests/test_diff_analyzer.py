import pytest
from datetime import datetime
from backend.schemas.github import PullRequestFullResponse, RepoInfo, PullRequestInfo, FileChange
from backend.core.diff_analyzer import analyze_pr

# Helper to build a minimal PullRequestFullResponse with a single Python file change
def make_mock_pr():
    repo = RepoInfo(
        owner="testowner",
        name="testrepo",
        description="Test repo",
        homepage=None,
        private=False,
        default_branch="main",
    )
    pr_info = PullRequestInfo(
        number=1,
        title="Add utility function",
        body="Adds a helper",
        state="open",
        merged=False,
        author="tester",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        merged_at=None,
    )
    # Diff adds a function and a try/except block, removes nothing.
    patch = (
        "@@ -0,0 +1,7 @@\n"
        "+def new_helper(x):\n"
        "+    try:\n"
        "+        return x * 2\n"
        "+    except Exception as e:\n"
        "+        raise ValueError('bad input') from e\n"
    )
    file_change = FileChange(
        filename="utils.py",
        status="added",
        additions=6,
        deletions=0,
        changes=6,
        patch=patch,
    )
    return PullRequestFullResponse(
        repository=repo,
        pull_request=pr_info,
        files=[file_change],
        commits=[],
        reviews=[],
    )

def test_analyze_pr_python_file():
    pr = make_mock_pr()
    ctx = analyze_pr(pr)
    assert ctx.total_files == 1
    assert ctx.total_added == 6
    assert ctx.total_removed == 0
    file_ctx = ctx.files[0]
    assert file_ctx.filename == "utils.py"
    assert file_ctx.language == "python"
    # The added function name should be detected
    assert "new_helper" in file_ctx.added_functions
    # Edge‑case keywords should be detected (try, except, raise)
    for kw in ["try", "except", "raise"]:
        assert kw in ctx.potential_edge_cases
    # Important concepts should include the function name
    assert "new_helper" in ctx.important_concepts
