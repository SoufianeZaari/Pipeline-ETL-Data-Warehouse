"""Load processed star-schema CSV files into the MySQL Data Warehouse."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from db_utils import BASE_DIR, get_dw_engine, normalize_blank, quote_identifier, run_sql_file, url_without_password


PROCESSED_DIR = BASE_DIR / "data" / "processed"
DW_SCHEMA = BASE_DIR / "sql" / "03_dw_schema.sql"

TABLE_LOAD_ORDER = [
    "dim_customer",
    "dim_product",
    "dim_date",
    "dim_region",
    "dim_payment",
    "dim_delivery",
    "quality_issues",
    "fact_sales",
]

TABLE_TRUNCATE_ORDER = [
    "fact_sales",
    "quality_issues",
    "dim_delivery",
    "dim_payment",
    "dim_region",
    "dim_date",
    "dim_product",
    "dim_customer",
]


def read_csv_rows(csv_path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        rows = [
            {column: normalize_blank(row[column]) for column in columns}
            for row in reader
        ]
    return columns, rows


def load_csv_mysql(conn: Any, table: str, csv_path: Path) -> int:
    columns, rows = read_csv_rows(csv_path)
    if not rows:
        return 0
    column_sql = ", ".join(quote_identifier(column) for column in columns)
    value_sql = ", ".join(f":{column}" for column in columns)
    stmt = text(f"INSERT INTO {quote_identifier(table)} ({column_sql}) VALUES ({value_sql})")
    result = conn.execute(stmt, rows)
    return int(result.rowcount or len(rows))


def load(processed_dir: Path = PROCESSED_DIR) -> dict[str, Any]:
    if not DW_SCHEMA.exists():
        raise FileNotFoundError(f"Schéma DW introuvable: {DW_SCHEMA}")

    run_sql_file(DW_SCHEMA)
    engine = get_dw_engine()
    summary: dict[str, int] = {}

    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for table in TABLE_TRUNCATE_ORDER:
            conn.execute(text(f"TRUNCATE TABLE {quote_identifier(table)}"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

        for table in TABLE_LOAD_ORDER:
            csv_path = processed_dir / f"{table}.csv"
            if not csv_path.exists():
                raise FileNotFoundError(f"Fichier traité manquant: {csv_path}")
            summary[table] = load_csv_mysql(conn, table, csv_path)

        db_counts = {
            table: conn.execute(text(f"SELECT COUNT(*) FROM {quote_identifier(table)}")).scalar_one()
            for table in TABLE_LOAD_ORDER
        }

    payload = {
        "database": url_without_password(engine.url),
        "loaded_rows": summary,
        "database_counts": db_counts,
    }
    (processed_dir / "load_summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Chargement MySQL DW terminé.")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload


def main() -> dict[str, Any]:
    try:
        return load()
    except SQLAlchemyError as exc:
        raise SystemExit(
            "Connexion MySQL DW impossible. Vérifiez que MySQL est démarré, "
            "copiez .env.example vers .env et renseignez MYSQL_PASSWORD / MEXORA_DW_URL.\n"
            f"Détail: {exc}"
        ) from exc


if __name__ == "__main__":
    main()
