"""PostgreSQL loader for the Mexora academic DWH — implements CDC-required functions."""

from __future__ import annotations

import logging

import pandas as pd
import sqlalchemy
from sqlalchemy import text


def charger_dimension(df: pd.DataFrame, table_name: str, engine: sqlalchemy.engine.Engine,
                      if_exists: str = "replace") -> None:
    """Load a dimension table into PostgreSQL.

    Uses TRUNCATE CASCADE + INSERT to preserve FK constraints defined in the schema.
    The `if_exists` parameter is accepted for API compatibility but always ignored.
    """
    with engine.connect() as conn:
        conn.execute(text(f"TRUNCATE TABLE dwh_mexora.{table_name} RESTART IDENTITY CASCADE"))
        conn.commit()

    df.to_sql(
        name=table_name,
        con=engine,
        schema="dwh_mexora",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )
    logging.info("[LOAD] %s: %s lignes chargées", table_name, len(df))


def charger_faits(df: pd.DataFrame, engine: sqlalchemy.engine.Engine) -> None:
    """Load the fact table — truncate then bulk insert."""
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE dwh_mexora.fait_ventes RESTART IDENTITY CASCADE"))
        conn.commit()

    df.to_sql(
        name="fait_ventes",
        con=engine,
        schema="dwh_mexora",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=5000,
    )
    logging.info("[LOAD] fait_ventes: %s lignes chargées", len(df))
