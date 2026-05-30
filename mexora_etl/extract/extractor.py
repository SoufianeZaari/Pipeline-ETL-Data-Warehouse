"""Extract academic Mexora raw sources into pandas DataFrames."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd


def extract_commandes(filepath: str | Path) -> pd.DataFrame:
    """Read `commandes_mexora.csv` exactly as raw text."""
    df = pd.read_csv(filepath, encoding="utf-8", dtype=str)
    logging.info("[EXTRACT] Commandes: %s lignes extraites depuis %s", len(df), filepath)
    return df


def extract_clients(filepath: str | Path) -> pd.DataFrame:
    """Read `clients_mexora.csv` exactly as raw text."""
    df = pd.read_csv(filepath, encoding="utf-8", dtype=str)
    logging.info("[EXTRACT] Clients: %s lignes extraites depuis %s", len(df), filepath)
    return df


def extract_regions(filepath: str | Path) -> pd.DataFrame:
    """Read the clean Moroccan regions reference file."""
    df = pd.read_csv(filepath, encoding="utf-8", dtype=str)
    logging.info("[EXTRACT] Régions: %s lignes extraites depuis %s", len(df), filepath)
    return df


def extract_produits(filepath: str | Path) -> pd.DataFrame:
    """Read `produits_mexora.json` and flatten the `produits` array."""
    with Path(filepath).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    df = pd.DataFrame(data["produits"])
    logging.info("[EXTRACT] Produits: %s lignes extraites depuis %s", len(df), filepath)
    return df

