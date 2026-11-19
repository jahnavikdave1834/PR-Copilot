"""Logging utilities using loguru.
Initialises a global logger based on settings.
"""

from loguru import logger
from pathlib import Path

from ..config.settings import settings

# Remove default logger to avoid duplicate output
logger.remove()

# Console sink
logger.add(
    sink=lambda msg: print(msg, end=""),  # simple stdout
    level=settings.log_level,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
)

# Optional file sink
if settings.log_path:
    logger.add(
        sink=str(settings.log_path),
        rotation="10 MB",
        retention="10 days",
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )

__all__ = ["logger"]

