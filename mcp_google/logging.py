import logging
import os
import sys
from typing import Optional


def setup_logging(
    log_file: Optional[str],
    level: int = logging.INFO,
    logger_name: str = "GoogleToolsMCP",
) -> logging.Logger:
    """Configure and return the named logger.

    Log level is controlled via the ``GOOGLE_LOG_LEVEL`` environment variable
    (or the ``log_level`` key in the YAML config). Defaults to INFO.
    """
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]

    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True,
    )

    return logging.getLogger(logger_name)
