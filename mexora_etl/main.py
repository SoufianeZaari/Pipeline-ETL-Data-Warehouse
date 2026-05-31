"""Pipeline ETL Mexora — orchestre Extract → Transform → Load vers PostgreSQL."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from mexora_etl.config.settings import ACADEMIC_RAW_DIR, LOG_DIR, get_pg_engine
from mexora_etl.extract.extractor import (
    extract_clients,
    extract_commandes,
    extract_produits,
    extract_regions,
)
from mexora_etl.load.loader import charger_dimension, charger_faits
from mexora_etl.transform.build_dimensions import (
    build_dim_client,
    build_dim_livreur,
    build_dim_produit,
    build_dim_region,
    build_dim_temps,
    build_fait_ventes,
)
from mexora_etl.transform.clean_clients import transform_clients
from mexora_etl.transform.clean_commandes import transform_commandes
from mexora_etl.transform.clean_produits import transform_produits
from mexora_etl.utils.logger import configure_logger


def run_pipeline() -> dict:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"etl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s — %(levelname)s — %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger(__name__)
    start = datetime.now()
    logger.info("=" * 60)
    logger.info("DÉMARRAGE PIPELINE ETL MEXORA")
    logger.info("=" * 60)

    # ------------------------------------------------------------------
    # 1. EXTRACT
    # ------------------------------------------------------------------
    logger.info("--- PHASE EXTRACT ---")
    df_commandes_raw = extract_commandes(str(ACADEMIC_RAW_DIR / "commandes_mexora.csv"))
    df_produits_raw = extract_produits(str(ACADEMIC_RAW_DIR / "produits_mexora.json"))
    df_clients_raw = extract_clients(str(ACADEMIC_RAW_DIR / "clients_mexora.csv"))
    df_regions = extract_regions(str(ACADEMIC_RAW_DIR / "regions_maroc.csv"))

    # ------------------------------------------------------------------
    # 2. TRANSFORM
    # ------------------------------------------------------------------
    logger.info("--- PHASE TRANSFORM ---")
    df_commandes = transform_commandes(df_commandes_raw, df_regions)
    df_clients = transform_clients(df_clients_raw)
    df_produits = transform_produits(df_produits_raw)

    dim_temps = build_dim_temps("2020-01-01", "2026-12-31")
    dim_client = build_dim_client(df_clients, df_commandes, df_regions)
    dim_produit = build_dim_produit(df_produits)
    dim_region = build_dim_region(df_regions)
    dim_livreur = build_dim_livreur(df_commandes)
    fait_ventes = build_fait_ventes(df_commandes, dim_temps, dim_client,
                                    dim_produit, dim_region, dim_livreur)

    # ------------------------------------------------------------------
    # 3. LOAD
    # ------------------------------------------------------------------
    logger.info("--- PHASE LOAD ---")
    engine = get_pg_engine()
    charger_dimension(dim_temps, "dim_temps", engine)
    charger_dimension(dim_client, "dim_client", engine)
    charger_dimension(dim_produit, "dim_produit", engine)
    charger_dimension(dim_region, "dim_region", engine)
    charger_dimension(dim_livreur, "dim_livreur", engine)
    charger_faits(fait_ventes, engine)

    duree = (datetime.now() - start).seconds
    logger.info("PIPELINE TERMINÉ EN %s secondes", duree)

    return {
        "commandes_raw": len(df_commandes_raw),
        "commandes_nettoyees": len(df_commandes),
        "clients_raw": len(df_clients_raw),
        "clients_nettoyes": len(df_clients),
        "produits_raw": len(df_produits_raw),
        "dim_temps": len(dim_temps),
        "dim_client": len(dim_client),
        "dim_produit": len(dim_produit),
        "dim_region": len(dim_region),
        "dim_livreur": len(dim_livreur),
        "fait_ventes": len(fait_ventes),
        "duree_secondes": duree,
    }


if __name__ == "__main__":
    summary = run_pipeline()
    print("\n=== RÉSUMÉ PIPELINE ===")
    for key, val in summary.items():
        print(f"  {key}: {val}")
