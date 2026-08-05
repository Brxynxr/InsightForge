import sys
from typing import Any

from loguru import logger

# Configure loguru
_level_handler = logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green>"
    " | <level>{level:<8}</level>"
    " | <cyan>{name}</cyan>"
    " - <level>{message}</level>",
    level="INFO",
)
_log_file_handler: Any = logger.add(
    "logs/promptforge.log",
    rotation="10 MB",
    retention="30 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name} | {message}",
)

# Ensure logger is exported
__all__ = ["logger"]
