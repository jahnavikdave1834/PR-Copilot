"""FastAPI application entry point.
Initialises the app, includes routers, and configures middlewares.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.logger.logger import logger as app_logger
from backend.api import health, github, assessment, reports

app = FastAPI(
    title="PR Understanding Copilot",
    version="1.0.0",
    description="Automated AI-driven PR understanding, technical interrogation, and intern evaluation.",
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(github.router, prefix="/api", tags=["github"])
app.include_router(assessment.router, prefix="/api", tags=["assessment"])
app.include_router(reports.router, prefix="/api", tags=["reports"])


@app.on_event("startup")
async def on_startup() -> None:
    app_logger.info("PR Understanding Copilot backend started")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    app_logger.info("PR Understanding Copilot backend shutting down")


__all__ = ["app"]
