"""Cleaning rules for the academic `produits_mexora.json` source."""

from __future__ import annotations

import logging

import pandas as pd


def transform_produits(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize product categories, prices, active flags and SCD-ready attributes."""
    df = df.copy()
    category_map = {
        "electronique": "Electronique",
        "électronique": "Electronique",
        "electronics": "Electronique",
        "mode": "Mode",
        "fashion": "Mode",
        "alimentation": "Alimentation",
        "food": "Alimentation",
    }
    df["categorie"] = df["categorie"].fillna("").str.lower().str.strip().map(category_map).fillna("Inconnue")
    df["prix_catalogue"] = pd.to_numeric(df["prix_catalogue"], errors="coerce")
    missing_prices = int(df["prix_catalogue"].isna().sum())
    medians = df.groupby("categorie")["prix_catalogue"].transform("median")
    df["prix_catalogue"] = df["prix_catalogue"].fillna(medians).fillna(100.0)
    df["date_creation"] = pd.to_datetime(df["date_creation"], format="mixed", dayfirst=True, errors="coerce")
    df["date_creation"] = df["date_creation"].fillna(pd.Timestamp("2024-01-01"))
    if "actif" not in df.columns:
        df["actif"] = True
    df["actif"] = (
        df["actif"]
        .fillna(True)
        .map(lambda value: str(value).strip().lower() not in {"0", "false", "faux", "non", "inactive", "inactif"})
    )
    df["date_debut"] = df["date_creation"].dt.date.astype(str)
    df["date_fin"] = "9999-12-31"
    df["est_actif"] = df["actif"].astype(int)
    logging.info("[TRANSFORM] Produits prix catalogue manquants corrigés: %s", missing_prices)
    logging.info("[TRANSFORM] Produits inactifs détectés: %s", int((~df["actif"]).sum()))
    return df
