"""Cleaning rules for the academic `commandes_mexora.csv` source."""

from __future__ import annotations

import logging

import pandas as pd


def charger_referentiel_villes(regions: pd.DataFrame) -> dict[str, str]:
    """Build a city normalization mapping from `regions_maroc.csv`."""
    mapping: dict[str, str] = {}
    aliases = {
        "tanger": "Tanger",
        "tng": "Tanger",
        "tnja": "Tanger",
        "tangier": "Tanger",
        "casa": "Casablanca",
        "cas": "Casablanca",
        "rabat": "Rabat",
    }
    for _, row in regions.iterrows():
        standard = str(row["nom_ville_standard"]).strip()
        mapping[standard.lower()] = standard
    mapping.update(aliases)
    return mapping


def transform_commandes(df: pd.DataFrame, regions: pd.DataFrame) -> pd.DataFrame:
    """Apply the mandatory command cleaning rules from the project statement."""
    initial = len(df)
    df = df.copy()

    before = len(df)
    df = df.drop_duplicates(subset=["id_commande"], keep="last")
    logging.info("[TRANSFORM] Commandes R1 doublons: %s lignes supprimées", before - len(df))

    df["date_commande"] = pd.to_datetime(df["date_commande"], format="mixed", dayfirst=True, errors="coerce")
    df["date_livraison"] = pd.to_datetime(df["date_livraison"], format="mixed", dayfirst=True, errors="coerce")
    invalid_dates = int(df["date_commande"].isna().sum())
    df = df.dropna(subset=["date_commande"])
    logging.info("[TRANSFORM] Commandes R2 dates: %s lignes supprimées", invalid_dates)

    mapping_villes = charger_referentiel_villes(regions)
    df["ville_livraison"] = (
        df["ville_livraison"].fillna("").astype(str).str.strip().str.lower().map(mapping_villes).fillna("Non renseignée")
    )

    mapping_statuts = {
        "livré": "livré",
        "livre": "livré",
        "delivered": "livré",
        "done": "livré",
        "ok": "en_cours",
        "ko": "annulé",
        "annulé": "annulé",
        "annule": "annulé",
        "cancelled": "annulé",
        "pending": "en_cours",
        "returned": "retourné",
        "retourné": "retourné",
        "retourne": "retourné",
    }
    status_key = df["statut"].fillna("").astype(str).str.strip().str.lower()
    df["statut"] = status_key.map(mapping_statuts).fillna("inconnu")
    logging.info("[TRANSFORM] Commandes R4 statuts inconnus: %s", int((df["statut"] == "inconnu").sum()))

    df["quantite"] = pd.to_numeric(df["quantite"], errors="coerce")
    df["prix_unitaire"] = pd.to_numeric(df["prix_unitaire"], errors="coerce")

    before = len(df)
    df = df[df["quantite"] > 0]
    logging.info("[TRANSFORM] Commandes R5 quantités: %s lignes supprimées", before - len(df))

    before = len(df)
    df = df[df["prix_unitaire"] > 0]
    logging.info("[TRANSFORM] Commandes R6 prix nuls: %s lignes supprimées", before - len(df))

    missing_livreur = int(df["id_livreur"].isna().sum() + (df["id_livreur"].fillna("").astype(str).str.strip() == "").sum())
    df["id_livreur"] = df["id_livreur"].fillna("").astype(str).str.strip().replace("", "-1")
    logging.info("[TRANSFORM] Commandes R7 livreurs manquants remplacés: %s", missing_livreur)
    logging.info("[TRANSFORM] Commandes: %s -> %s lignes", initial, len(df))
    return df

