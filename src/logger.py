"""
logger.py
---------
Centralized logging setup for the transcript analyzer.
Creates a rotating log file per run + a console handler.
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logger(name: str = "transcript_agent", log_dir: str = "logs") -> logging.Logger:
    """
    Create and return a logger with:
    - Console handler at INFO level
    - Rotating file handler at DEBUG level (10 MB x 5 backups)

    Args:
        name:    Logger name (module-level grouping)
        log_dir: Directory where .log files are written (auto-created)

    Returns:
        Configured logging.Logger instance
    """
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"run_{timestamp}.log")

    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)-5s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # --- Console handler (INFO and above) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    # --- Rotating file handler (DEBUG and above) ---
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.debug(f"Logger initialized — writing to: {log_file}")
    return logger
