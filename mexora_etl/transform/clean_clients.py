"""Cleaning rules for the academic `clients_mexora.csv` source."""

from __future__ import annotations

import logging
import re
from datetime import date

import pandas as pd


EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def transform_clients(df: pd.DataFrame) -> pd.DataFrame:
    """Clean clients and create normalized age and gender attributes."""
    initial = len(df)
    df = df.copy()
    df["email_norm"] = df["email"].fillna("").str.lower().str.strip()
    df["date_inscription_parsed"] = pd.to_datetime(df["date_inscription"], format="mixed", dayfirst=True, errors="coerce")
    df = df.sort_values("date_inscription_parsed").drop_duplicates(subset=["email_norm"], keep="last")
    logging.info("[TRANSFORM] Clients R1 doublons email: %s supprimés", initial - len(df))

    mapping_sexe = {
        "m": "m",
        "male": "m",
        "homme": "m",
        "h": "m",
        "1": "m",
        "f": "f",
        "female": "f",
        "femme": "f",
        "0": "f",
    }
    df["sexe"] = df["sexe"].fillna("").str.lower().str.strip().map(mapping_sexe).fillna("inconnu")

    df["date_naissance"] = pd.to_datetime(df["date_naissance"], format="mixed", dayfirst=True, errors="coerce")
    today = pd.Timestamp(date.today())
    df["age"] = ((today - df["date_naissance"]).dt.days // 365).astype("float")
    invalid_age = (df["age"] < 16) | (df["age"] > 100)
    df.loc[invalid_age, "date_naissance"] = pd.NaT
    df.loc[invalid_age, "age"] = pd.NA
    df["tranche_age"] = pd.cut(
        df["age"].fillna(0),
        bins=[0, 18, 25, 35, 45, 55, 65, 200],
        labels=["<18", "18-24", "25-34", "35-44", "45-54", "55-64", "65+"],
    ).astype(str)

    invalid_email = ~df["email"].fillna("").map(lambda value: bool(EMAIL_PATTERN.match(str(value))))
    df.loc[invalid_email, "email"] = pd.NA
    logging.info("[TRANSFORM] Clients R4 emails invalides: %s", int(invalid_email.sum()))
    return df

