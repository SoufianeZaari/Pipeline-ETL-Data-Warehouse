"""Extract Mexora OLTP data from MySQL into data/raw CSV files."""

from __future__ import annotations

import csv
import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from db_utils import BASE_DIR, get_oltp_engine, quote_identifier, url_without_password


RAW_DIR = BASE_DIR / "data" / "raw"
TABLES = ["customers", "products", "orders", "order_items", "payments", "deliveries", "returns"]


def serialize(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def write_rows(path: Path, columns: list[str], rows: list[tuple]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)


def extract_from_mysql(raw_dir: Path = RAW_DIR) -> dict[str, int]:
    """Read MySQL OLTP tables and write one raw CSV per table."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    engine = get_oltp_engine()
    summary: dict[str, int] = {}

    with engine.connect() as conn:
        for table in TABLES:
            result = conn.execute(text(f"SELECT * FROM {quote_identifier(table)}"))
            columns = list(result.keys())
            rows = [tuple(serialize(value) for value in row) for row in result.fetchall()]
            write_rows(raw_dir / f"{table}.csv", columns, rows)
            summary[table] = len(rows)

    log_payload = {
        "extracted_at": datetime.now().isoformat(timespec="seconds"),
        "source": url_without_password(engine.url),
        "destination": str(raw_dir.relative_to(BASE_DIR)),
        "tables": summary,
    }
    (raw_dir / "extract_summary.json").write_text(json.dumps(log_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    with (raw_dir / "extract.log").open("w", encoding="utf-8") as handle:
        handle.write(f"Extraction Mexora depuis MySQL - {log_payload['extracted_at']}\n")
        handle.write(f"Source: {log_payload['source']}\n")
        for table, row_count in summary.items():
            handle.write(f"{table}: {row_count} lignes\n")
    return summary


def main() -> dict[str, int]:
    try:
        summary = extract_from_mysql()
    except SQLAlchemyError as exc:
        raise SystemExit(
            "Connexion MySQL OLTP impossible. Vérifiez que MySQL est démarré, "
            "copiez .env.example vers .env et renseignez MYSQL_PASSWORD / MEXORA_SOURCE_URL.\n"
            f"Détail: {exc}"
        ) from exc
    print("Extraction MySQL terminée.")
    for table, row_count in summary.items():
        print(f"- {table}: {row_count}")
    return summary


if __name__ == "__main__":
    main()
