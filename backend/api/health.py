from fastapi import APIRouter
from loguru import logger

router = APIRouter()

@router.get("/health", summary="Health check endpoint")
async def health_check() -> dict:
    """Simple health endpoint returning service status.
    Returns a JSON payload with a static message and the current server time.
    """
    logger.info("Health check requested")
    return {"status": "ok", "message": "PR Understanding Copilot backend is alive"}

