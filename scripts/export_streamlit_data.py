"""Export PostgreSQL DWH data to CSV files for the Streamlit dashboard.

Run this script once (or after each ETL refresh) to generate the CSV files
that dashboard/streamlit_app.py reads.  The app works fully offline / on
Streamlit Cloud from these CSVs — no live PostgreSQL connection needed.

Usage:
    python scripts/export_streamlit_data.py

Environment variable (optional):
    MEXORA_PG_URL   postgresql+psycopg2://user@/db?host=/socket&port=5433
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import pandas as pd
    from sqlalchemy import create_engine, text
except ImportError as exc:
    print(f"[ERROR] Missing dependency: {exc}")
    print("Run: pip install pandas sqlalchemy psycopg2-binary")
    sys.exit(1)

OUTPUT_DIR = PROJECT_ROOT / "dashboard" / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PG_URL = os.getenv(
    "MEXORA_PG_URL",
    f"postgresql+psycopg2://{os.getenv('USER', 'soufiane')}"
    f"@/mexora_dwh?host=/tmp/mexora_pg_socket&port=5433",
)


def get_engine():
    try:
        engine = create_engine(PG_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as exc:
        print("\n[ERROR] Impossible de se connecter a PostgreSQL.")
        print(f"  URL utilisee : {PG_URL}")
        print(f"  Detail       : {exc}")
        print("\n  --> Verifiez que PostgreSQL local tourne :")
        print("      /usr/lib/postgresql/16/bin/pg_ctl \\")
        print("        -D /tmp/mexora_pg_data \\")
        print("        -o \"-p 5433 -k /tmp/mexora_pg_socket\" start")
        print("  --> Puis relancez : python scripts/export_streamlit_data.py")
        sys.exit(1)


def export(engine, query: str, filename: str) -> int:
    try:
        df = pd.read_sql(query, engine)
        path = OUTPUT_DIR / filename
        df.to_csv(path, index=False)
        print(f"  [OK] {filename:45s}  {len(df):>6} lignes")
        return len(df)
    except Exception as exc:
        print(f"  [WARN] {filename}: {exc}")
        return 0


def main():
    print("=" * 60)
    print("EXPORT DONNEES STREAMLIT — Mexora DWH PostgreSQL")
    print("=" * 60)

    engine = get_engine()
    total = 0

    # ---- KPIs globaux ----
    total += export(engine, """
        SELECT
            SUM(montant_ttc)                                   AS ca_total,
            COUNT(DISTINCT id_commande)                        AS nb_commandes,
            COUNT(DISTINCT id_client)                          AS nb_clients,
            ROUND(SUM(montant_ttc) /
                  NULLIF(COUNT(DISTINCT id_commande), 0), 2)   AS panier_moyen,
            ROUND(
                COUNT(*) FILTER (WHERE statut_commande = 'retourné') * 100.0
                / NULLIF(COUNT(*), 0), 2)                      AS taux_retour_pct,
            ROUND(AVG(delai_livraison_jours), 2)               AS delai_moyen_jours
        FROM dwh_mexora.fait_ventes
        WHERE statut_commande IN ('livré','retourné','en_cours','annulé')
    """, "kpis.csv")

    # ---- CA mensuel (depuis vue matérialisée) ----
    total += export(engine, """
        SELECT annee, mois, libelle_mois, periode_ramadan,
               region_admin, zone_geo, categorie,
               ca_ttc, nb_commandes, volume_vendu, panier_moyen, nb_clients_actifs
        FROM reporting_mexora.mv_ca_mensuel
        ORDER BY annee, mois
    """, "ca_mensuel.csv")

    # ---- CA par région (agrégé) ----
    total += export(engine, """
        SELECT r.region_admin, r.ville, r.zone_geo,
               SUM(f.montant_ttc)                               AS ca_ttc,
               COUNT(DISTINCT f.id_commande)                    AS nb_commandes,
               COUNT(DISTINCT f.id_client)                      AS nb_clients,
               ROUND(AVG(f.montant_ttc), 2)                     AS panier_moyen
        FROM dwh_mexora.fait_ventes f
        JOIN dwh_mexora.dim_region r ON f.id_region = r.id_region
        WHERE f.statut_commande = 'livré'
        GROUP BY r.region_admin, r.ville, r.zone_geo
        ORDER BY ca_ttc DESC
    """, "ca_region.csv")

    # ---- Top produits à Tanger ----
    total += export(engine, """
        SELECT p.nom_produit, p.categorie, p.marque,
               SUM(f.quantite_vendue)  AS qte_totale,
               SUM(f.montant_ttc)      AS ca_total
        FROM dwh_mexora.fait_ventes f
        JOIN dwh_mexora.dim_produit p ON f.id_produit = p.id_produit_sk
        JOIN dwh_mexora.dim_region  r ON f.id_region  = r.id_region
        WHERE f.statut_commande = 'livré'
          AND r.ville = 'Tanger'
        GROUP BY p.nom_produit, p.categorie, p.marque
        ORDER BY ca_total DESC
        LIMIT 20
    """, "top_produits_tanger.csv")

    # ---- Segments clients ----
    # Note: with 50 000 synthetic orders the per-client CA far exceeds
    # the 15 000 MAD Gold threshold, collapsing all clients into Gold.
    # We recompute segments using percentile-based thresholds so the
    # Streamlit visualisation shows a realistic Gold/Silver/Bronze split.
    # The DWH data is NOT modified — this is only for the dashboard export.
    total += export(engine, """
        WITH ca_client AS (
            SELECT f.id_client,
                   SUM(f.montant_ttc) AS ca_12m
            FROM dwh_mexora.fait_ventes f
            WHERE f.statut_commande = 'livré'
            GROUP BY f.id_client
        ),
        seuils AS (
            SELECT PERCENTILE_CONT(0.70) WITHIN GROUP (ORDER BY ca_12m) AS seuil_gold,
                   PERCENTILE_CONT(0.30) WITHIN GROUP (ORDER BY ca_12m) AS seuil_silver
            FROM ca_client
        ),
        segments AS (
            SELECT ca.id_client,
                   CASE
                     WHEN ca.ca_12m >= s.seuil_gold   THEN 'Gold'
                     WHEN ca.ca_12m >= s.seuil_silver  THEN 'Silver'
                     ELSE 'Bronze'
                   END AS segment_client
            FROM ca_client ca
            CROSS JOIN seuils s
        )
        SELECT sg.segment_client,
               COUNT(DISTINCT f.id_commande)                       AS nb_commandes,
               COUNT(DISTINCT sg.id_client)                        AS nb_clients,
               ROUND(SUM(f.montant_ttc), 2)                        AS ca_total,
               ROUND(SUM(f.montant_ttc)
                     / NULLIF(COUNT(DISTINCT f.id_commande), 0), 2) AS panier_moyen,
               ROUND(SUM(f.montant_ttc) * 100.0
                     / SUM(SUM(f.montant_ttc)) OVER (), 2)         AS pct_ca
        FROM dwh_mexora.fait_ventes f
        JOIN segments sg ON f.id_client = sg.id_client
        WHERE f.statut_commande = 'livré'
        GROUP BY sg.segment_client
        ORDER BY panier_moyen DESC
    """, "segments_clients.csv")

    # ---- Taux de retour par catégorie ----
    total += export(engine, """
        SELECT p.categorie,
               COUNT(*)                                        AS nb_total,
               COUNT(*) FILTER (WHERE f.statut_commande = 'retourné') AS nb_retours,
               ROUND(
                   COUNT(*) FILTER (WHERE f.statut_commande = 'retourné') * 100.0
                   / NULLIF(COUNT(*), 0), 2)                   AS taux_retour_pct
        FROM dwh_mexora.fait_ventes f
        JOIN dwh_mexora.dim_produit p ON f.id_produit = p.id_produit_sk
        GROUP BY p.categorie
        ORDER BY taux_retour_pct DESC
    """, "taux_retour_categorie.csv")

    # ---- Effet Ramadan (alimentation) ----
    total += export(engine, """
        SELECT
            t.annee, t.mois, t.libelle_mois, t.periode_ramadan,
            SUM(f.montant_ttc)     AS ca_ttc,
            SUM(f.quantite_vendue) AS volume_vendu
        FROM dwh_mexora.fait_ventes f
        JOIN dwh_mexora.dim_temps   t ON f.id_date    = t.id_date
        JOIN dwh_mexora.dim_produit p ON f.id_produit = p.id_produit_sk
        WHERE p.categorie = 'Alimentation'
        GROUP BY t.annee, t.mois, t.libelle_mois, t.periode_ramadan
        ORDER BY t.annee, t.mois
    """, "ramadan_food.csv")

    # ---- Livraisons & retours (performance livreurs) ----
    total += export(engine, """
        SELECT l.nom_livreur, l.type_transport, l.zone_couverture,
               COUNT(*)                                                AS nb_livraisons,
               ROUND(AVG(f.delai_livraison_jours), 2)                 AS delai_moyen,
               COUNT(*) FILTER (WHERE f.delai_livraison_jours > 3)    AS nb_retards,
               ROUND(COUNT(*) FILTER (WHERE f.delai_livraison_jours > 3)
                     * 100.0 / NULLIF(COUNT(*), 0), 2)                AS taux_retard_pct,
               COUNT(*) FILTER (WHERE f.statut_commande = 'retourné') AS nb_retours
        FROM dwh_mexora.fait_ventes f
        JOIN dwh_mexora.dim_livreur l ON f.id_livreur = l.id_livreur
        WHERE f.statut_commande IN ('livré', 'retourné')
          AND f.delai_livraison_jours IS NOT NULL
        GROUP BY l.nom_livreur, l.type_transport, l.zone_couverture
        ORDER BY delai_moyen ASC
    """, "livraison_retours.csv")

    print("-" * 60)
    print(f"Export termine : {total} lignes totales dans {OUTPUT_DIR}")
    print(f"Dossier : {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
