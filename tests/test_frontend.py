import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from frontend.api_client import BackendClient

APP_FILE = str(Path(__file__).resolve().parent.parent / "frontend" / "app.py")


def test_api_client_endpoints():
    client = BackendClient("http://testserver/api")

    with patch("httpx.Client.get") as mock_get, patch("httpx.Client.post") as mock_post:
        # 1. Health
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"status": "ok"})
        res = client.check_health()
        assert res["status"] == "ok"

        # 2. Fetch PR
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"repository": {"name": "test"}})
        pr = client.fetch_pr("https://github.com/owner/repo", 1)
        assert pr["repository"]["name"] == "test"

        # 3. Generate Assessment
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"assessment_id": 42, "questions": []})
        gen = client.generate_assessment("https://github.com/owner/repo", 1, "intern_1")
        assert gen["assessment_id"] == 42

        # 4. Submit Assessment
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"report_id": 100, "report": {"total_score": 25}})
        sub = client.submit_assessment(42, {"1": "My answer"})
        assert sub["report_id"] == 100

        # 5. List Assessments
        mock_get.return_value = MagicMock(status_code=200, json=lambda: [{"id": 1, "intern_id": "intern_1"}])
        all_assessments = client.list_assessments()
        assert len(all_assessments) == 1

        # 6. Get Report
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"report": {"percentage": 85.0}})
        rep = client.get_report(42)
        assert rep["report"]["percentage"] == 85.0


def _mock_get_response(url, *args, **kwargs):
    url_str = str(url)
    if "health" in url_str:
        return MagicMock(status_code=200, json=lambda: {"status": "ok"})
    if "reports" in url_str:
        return MagicMock(
            status_code=200,
            json=lambda: {"report": {"percentage": 85.0, "total_score": 25, "max_score": 30, "passed": True, "dimension_scores": {}}},
        )
    if "/assessment/" in url_str:
        return MagicMock(
            status_code=200,
            json=lambda: {"id": 1, "intern_id": "intern_alex@company.com", "repo_url": "https://github.com/fastapi/fastapi", "pr_number": 1, "questions": []},
        )
    # Default list for assessments (/assessments)
    return MagicMock(status_code=200, json=lambda: [])


def test_streamlit_views_navigation():
    from streamlit.testing.v1 import AppTest

    views = [
        "Home Dashboard",
        "New PR Assessment",
        "PR Details & Changes",
        "Intern Q&A Interface",
        "Assessment Results",
        "Mentor Dashboard",
        "Assessment History",
    ]

    with patch("httpx.Client.get", side_effect=_mock_get_response), patch("httpx.Client.post") as mock_post:
        for view in views:
            at = AppTest.from_file(APP_FILE)
            at.run(timeout=10)
            at.sidebar.radio[0].set_value(view).run(timeout=10)
            assert len(at.exception) == 0, f"Exception in view {view}"


def test_streamlit_seeded_assessment_flow():
    from streamlit.testing.v1 import AppTest

    with patch("httpx.Client.get", side_effect=_mock_get_response), patch("httpx.Client.post") as mock_post:
        at = AppTest.from_file(APP_FILE)
        at.run(timeout=10)
        assert len(at.exception) == 0

        # Set assessment ID #1 and verify Results view
        at.session_state["current_assessment_id"] = 1
        at.sidebar.radio[0].set_value("Assessment Results").run(timeout=10)
        assert len(at.exception) == 0

        # Verify Intern Q&A view
        at.sidebar.radio[0].set_value("Intern Q&A Interface").run(timeout=10)
        assert len(at.exception) == 0

