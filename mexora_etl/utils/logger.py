"""Logging helpers for the academic Mexora ETL package."""

from __future__ import annotations

import logging
from datetime import datetime

from mexora_etl.config.settings import LOG_DIR


def configure_logger(name: str = "mexora_etl") -> logging.Logger:
    """Create a console and file logger for ETL operations."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler = logging.FileHandler(
        LOG_DIR / f"etl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

