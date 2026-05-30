"""Central settings for the academic Mexora ETL package."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ACADEMIC_RAW_DIR = PROJECT_ROOT / "data" / "academic_raw"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LOG_DIR = PROJECT_ROOT / "logs"


def load_settings() -> dict[str, str]:
    """Load environment variables used by the validated MySQL pipeline."""
    load_dotenv(PROJECT_ROOT / ".env")
    return {
        "mysql_host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "mysql_port": os.getenv("MYSQL_PORT", "3307"),
        "mysql_user": os.getenv("MYSQL_USER", "mexora_user"),
        "mysql_database_oltp": os.getenv("MEXORA_OLTP_DB", "mexora_oltp"),
        "mysql_database_dw": os.getenv("MEXORA_DW_DB", "mexora_dw"),
        "source_url": os.getenv(
            "MEXORA_SOURCE_URL",
            "mysql+pymysql://mexora_user:mexora_pass@127.0.0.1:3307/mexora_oltp",
        ),
        "dw_url": os.getenv(
            "MEXORA_DW_URL",
            "mysql+pymysql://mexora_user:mexora_pass@127.0.0.1:3307/mexora_dw",
        ),
    }

