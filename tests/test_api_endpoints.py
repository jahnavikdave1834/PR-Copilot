import json
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.db.database import init_db
from tests.test_github_service import make_dummy_pr


@pytest.fixture(autouse=True)
def init_test_db():
    init_db()


def test_api_health_endpoint():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_github_fetch_pr():
    client = TestClient(app)
    dummy_pr = make_dummy_pr()

    with patch("backend.api.github.fetch_pr_data", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = dummy_pr
        payload = {
            "repo_url": "https://github.com/fastapi/fastapi",
            "pr_number": 1,
        }
        response = client.post("/api/github/fetch-pr", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["repository"]["name"] == "repo"
        assert data["pull_request"]["title"] == "Test PR"


def test_api_assessment_lifecycle():
    client = TestClient(app)
    dummy_pr = make_dummy_pr()

    from backend.schemas.question import Question
    mock_questions = [
        Question(
            text="How does error handling work?",
            category="edge_case",
            difficulty="medium",
            evidence=[],
            expected_answer_concepts=["try-except", "ValueError"],
            evaluation_criteria=[],
        )
    ]

    # 1. POST /api/assessment/generate
    with patch("backend.api.assessment.fetch_pr_data", new_callable=AsyncMock) as mock_fetch, \
         patch("backend.api.assessment.generate_questions", new_callable=AsyncMock) as mock_gen:
        mock_fetch.return_value = dummy_pr
        mock_gen.return_value = mock_questions

        gen_resp = client.post(
            "/api/assessment/generate",
            json={
                "repo_url": "https://github.com/fastapi/fastapi",
                "pr_number": 1,
                "intern_id": "intern_alex@test.com",
            },
        )
        assert gen_resp.status_code == 200
        gen_data = gen_resp.json()
        assert "assessment_id" in gen_data
        assessment_id = gen_data["assessment_id"]
        assert len(gen_data["questions"]) == 1
        question_id = gen_data["questions"][0]["id"]

    # 2. GET /api/assessment/{assessment_id}
    get_resp = client.get(f"/api/assessment/{assessment_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["id"] == assessment_id
    assert len(get_data["questions"]) == 1

    # 3. POST /api/assessment/submit
    submit_resp = client.post(
        "/api/assessment/submit",
        json={
            "assessment_id": assessment_id,
            "answers": {
                str(question_id): "The code uses try-except to raise a ValueError upon bad input.",
            },
        },
    )
    assert submit_resp.status_code == 200
    submit_data = submit_resp.json()
    assert "report_id" in submit_data
    assert submit_data["report"]["total_score"] > 0

    # 4. GET /api/reports/{assessment_id}
    report_resp = client.get(f"/api/reports/{assessment_id}")
    assert report_resp.status_code == 200
    report_data = report_resp.json()
    assert report_data["assessment_id"] == assessment_id
    assert "total_score" in report_data["report"]
