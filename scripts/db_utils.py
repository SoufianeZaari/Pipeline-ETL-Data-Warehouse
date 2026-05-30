"""Shared MySQL and environment helpers for the Mexora ETL pipeline."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL, make_url


BASE_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BASE_DIR / ".env"


def load_env(env_file: Path = ENV_FILE) -> None:
    """Load .env values without requiring python-dotenv at runtime."""
    try:
        from dotenv import load_dotenv

        load_dotenv(env_file)
        return
    except ImportError:
        pass

    if not env_file.exists():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def mysql_url_from_env(database: str | None = None) -> URL:
    load_env()
    return URL.create(
        "mysql+pymysql",
        username=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=database,
    )


def get_engine(env_var: str, fallback_database_env: str) -> Engine:
    load_env()
    explicit_url = os.getenv(env_var)
    if explicit_url:
        return create_engine(explicit_url, future=True)
    default_database = "mexora_oltp" if fallback_database_env == "MEXORA_OLTP_DB" else "mexora_dw"
    database = os.getenv(fallback_database_env, default_database)
    return create_engine(mysql_url_from_env(database), future=True)


def get_server_engine() -> Engine:
    return create_engine(mysql_url_from_env(None), future=True)


def get_oltp_engine() -> Engine:
    return get_engine("MEXORA_SOURCE_URL", "MEXORA_OLTP_DB")


def get_dw_engine() -> Engine:
    return get_engine("MEXORA_DW_URL", "MEXORA_DW_DB")


def quote_identifier(identifier: str) -> str:
    return "`" + identifier.replace("`", "``") + "`"


def clean_sql_statement(statement: str) -> str:
    lines = []
    for line in statement.splitlines():
        stripped = line.strip()
        if stripped.startswith("--") or stripped.startswith("#"):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def split_sql_script(sql: str) -> list[str]:
    """Split a simple MySQL script into statements.

    The project SQL files do not define stored procedures or custom delimiters,
    so semicolon splitting is sufficient and avoids enabling multi-statements.
    """
    statements = []
    for chunk in sql.split(";"):
        statement = clean_sql_statement(chunk)
        if statement:
            statements.append(statement)
    return statements


def run_sql_file(path: Path, engine: Engine | None = None) -> None:
    selected_engine = engine or get_server_engine()
    sql = path.read_text(encoding="utf-8")
    with selected_engine.connect() as conn:
        for statement in split_sql_script(sql):
            conn.execute(text(statement))
        conn.commit()


def normalize_blank(value: Any) -> Any:
    if value == "":
        return None
    return value


def url_without_password(url: str | URL) -> str:
    parsed = make_url(str(url))
    if parsed.password:
        parsed = parsed.set(password="***")
    return str(parsed)
