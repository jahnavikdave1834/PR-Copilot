"""Application settings loaded from environment variables.
Uses pydantic BaseSettings for type validation and defaults.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, List

from pydantic_settings import BaseSettings
from pydantic import Field, HttpUrl, validator

class Settings(BaseSettings):
    """Global configuration for the PR Understanding Copilot backend.
    All values are sourced from a ``.env`` file (or the OS environment).
    """

    # FastAPI host configuration
    host: str = Field("0.0.0.0", description="Host address for the server")
    port: int = Field(8000, ge=1, le=65535, description="Port number for the server")

    # Logging configuration
    log_level: str = Field("INFO", description="Log level for loguru")
    log_path: Optional[Path] = Field(
        default=None,
        description="Optional path to a rotating log file. If omitted, logs go to stdout only.",
    )

    # External services
    github_token: Optional[str] = Field(
        default=None,
        description="Personal access token for GitHub API (required for private repos).",
    )
    groq_api_key: Optional[str] = Field(
        default=None,
        description="API key for Groq LLM service.",
    )

    # Database
    sqlite_url: str = Field(
        "sqlite:///./pr_copilot.db",
        description="SQLAlchemy connection URL for SQLite persistence.",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("log_level")
    def _validate_log_level(cls, v: str) -> str:
        allowed = {"TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"Invalid log level: {v}. Choose from {sorted(allowed)}")
        return v.upper()

# Export a singleton settings instance for the whole app
settings = Settings()

