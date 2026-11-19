"""Configuration and thin wrapper for the Groq LLM API.
Only the chat/completions endpoint is used. The client is async and respects
the ``GROQ_API_KEY`` environment variable defined in ``backend.config.settings``.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import httpx
from loguru import logger

from ..config.settings import settings

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "mixtral-8x7b-32768"
TIMEOUT = 30.0  # seconds for LLM calls – longer than ordinary GitHub calls


class GroqClient:
    """Simple async client for Groq chat completions.
    The ``chat`` method expects a list of ``messages`` as per the OpenAI API spec.
    """

    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or settings.groq_api_key
        if not self.api_key:
            raise RuntimeError("Groq API key not configured – set GROQ_API_KEY in .env")
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(timeout=TIMEOUT, headers=self.headers)

    async def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 4096,
        }
        logger.debug("Sending request to Groq: model={}, messages_count={}", self.model, len(messages))
        try:
            resp = await self.client.post(GROQ_ENDPOINT, json=payload)
        except httpx.RequestError as exc:
            logger.error("Network error when contacting Groq: {}", exc)
            raise RuntimeError(f"Groq request failed: {exc}") from exc
        if resp.status_code != 200:
            logger.error("Groq API error {}: {}", resp.status_code, resp.text)
            raise RuntimeError(f"Groq API returned {resp.status_code}: {resp.text}")
        try:
            data = resp.json()
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON from Groq: {}", exc)
            raise RuntimeError("Groq returned non‑JSON response") from exc
        return data

    async def close(self) -> None:
        await self.client.aclose()


def get_groq_client() -> GroqClient:
    """Factory used by FastAPI dependencies – returns a client bound to the current settings."""
    return GroqClient()

