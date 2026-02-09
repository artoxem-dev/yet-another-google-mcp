import logging
import os
import sys
from typing import Optional


def setup_logging(
    log_file: Optional[str],
    level: int = logging.INFO,
    logger_name: str = "GoogleToolsMCP",
) -> logging.Logger:
    handlers = [logging.StreamHandler(sys.stderr)]

    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

    return logging.getLogger(logger_name)
