"""API Client for interacting with the FastAPI backend.
All requests from Streamlit to the backend go through this client.
"""

from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional


class BackendClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000/api"):
        self.base_url = base_url.rstrip("/")

    def _get(self, endpoint: str, timeout: float = 15.0) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url)
            if resp.status_code >= 400:
                try:
                    err_json = resp.json()
                    detail = err_json.get("detail", resp.text)
                except Exception:
                    detail = resp.text or f"HTTP {resp.status_code}"
                raise RuntimeError(detail)
            return resp.json()

    def _post(self, endpoint: str, json_data: Dict[str, Any], timeout: float = 60.0) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=json_data)
            if resp.status_code >= 400:
                try:
                    err_json = resp.json()
                    detail = err_json.get("detail", resp.text)
                except Exception:
                    detail = resp.text or f"HTTP {resp.status_code}"
                raise RuntimeError(detail)
            return resp.json()

    def check_health(self) -> Dict[str, Any]:
        return self._get("/health", timeout=5.0)

    def fetch_pr(self, repo_url: str, pr_number: int) -> Dict[str, Any]:
        return self._post("/github/fetch-pr", {"repo_url": repo_url, "pr_number": pr_number})

    def generate_assessment(self, repo_url: str, pr_number: int, intern_id: str) -> Dict[str, Any]:
        return self._post(
            "/assessment/generate",
            {"repo_url": repo_url, "pr_number": pr_number, "intern_id": intern_id},
            timeout=120.0,
        )

    def submit_assessment(self, assessment_id: int, answers: Dict[str, str]) -> Dict[str, Any]:
        return self._post(
            "/assessment/submit",
            {"assessment_id": assessment_id, "answers": answers},
            timeout=120.0,
        )

    def get_assessment(self, assessment_id: int) -> Dict[str, Any]:
        return self._get(f"/assessment/{assessment_id}")

    def list_assessments(self) -> List[Dict[str, Any]]:
        return self._get("/assessments")

    def get_report(self, assessment_id: int) -> Dict[str, Any]:
        return self._get(f"/reports/{assessment_id}")
