"""Run the complete MySQL-based Mexora ETL pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import extract
import generate_data
import load
import transform
from db_utils import BASE_DIR, load_env
from start_project_mysql import ensure_project_mysql
from sqlalchemy.exc import SQLAlchemyError


def run_pipeline(regenerate: bool = False, skip_generate: bool = False) -> dict[str, Any]:
    load_env()
    ensure_project_mysql()

    if regenerate or not skip_generate:
        print("1/4 Génération des données et chargement MySQL OLTP")
        generated_summary = generate_data.main(load_mysql=True)
    else:
        generated_summary = {"status": "generation_skipped"}

    print("2/4 Extraction MySQL OLTP vers data/raw")
    extraction_summary = extract.extract_from_mysql()

    print("3/4 Transformation vers data/processed")
    transformation_summary = transform.transform()

    print("4/4 Chargement MySQL Data Warehouse")
    load_summary = load.load()

    generated_rows = generated_summary.get("generated_rows", {})
    final_summary = {
        "generated": generated_summary,
        "extracted": extraction_summary,
        "processed": transformation_summary["processed_rows"],
        "quality_actions": transformation_summary["quality_actions"],
        "loaded": load_summary["database_counts"],
    }
    summary_path = BASE_DIR / "data" / "processed" / "etl_summary.json"
    summary_path.write_text(json.dumps(final_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\nRésumé final ETL Mexora")
    print(f"- clients générés: {generated_rows.get('customers', 0)}")
    print(f"- produits générés: {generated_rows.get('products', 0)}")
    print(f"- commandes générées: {generated_rows.get('orders', 0)}")
    print(f"- lignes order_items générées: {generated_rows.get('order_items', 0)}")
    print(f"- paiements générés: {generated_rows.get('payments', 0)}")
    print(f"- livraisons générées: {generated_rows.get('deliveries', 0)}")
    print(f"- retours générés: {generated_rows.get('returns', 0)}")
    print(f"- clients extraits: {extraction_summary.get('customers', 0)}")
    print(f"- commandes extraites: {extraction_summary.get('orders', 0)}")
    print(f"- lignes fact_sales: {load_summary['database_counts'].get('fact_sales', 0)}")
    print(f"- anomalies détectées: {transformation_summary['processed_rows'].get('quality_issues', 0)}")
    print(f"- anomalies corrigées: {transformation_summary['quality_actions'].get('corrected', 0)}")
    print(f"- anomalies supprimées: {transformation_summary['quality_actions'].get('removed', 0)}")
    print(f"- Data Warehouse MySQL: {load_summary['database']}")
    return final_summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pipeline ETL complet Mexora avec MySQL.")
    parser.add_argument("--regenerate", action="store_true", help="Regénère les données et recharge MySQL OLTP.")
    parser.add_argument("--skip-generate", action="store_true", help="Réutilise la source MySQL OLTP existante.")
    return parser.parse_args()


def main() -> dict[str, Any]:
    args = parse_args()
    try:
        return run_pipeline(regenerate=args.regenerate, skip_generate=args.skip_generate)
    except SQLAlchemyError as exc:
        raise SystemExit(
            "Pipeline arrêté: connexion MySQL impossible. Vérifiez MySQL, puis créez .env avec "
            "MYSQL_PASSWORD, MEXORA_SOURCE_URL et MEXORA_DW_URL.\n"
            f"Détail: {exc}"
        ) from exc


if __name__ == "__main__":
    main()
