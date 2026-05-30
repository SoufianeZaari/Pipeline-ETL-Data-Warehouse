"""Build academic dimensions and fact table from cleaned DataFrames."""

from __future__ import annotations

import pandas as pd


def build_dim_temps(date_debut: str, date_fin: str) -> pd.DataFrame:
    """Generate a complete time dimension with Moroccan holidays and Ramadan."""
    dates = pd.date_range(start=date_debut, end=date_fin, freq="D")
    feries_maroc = {
        "2024-01-01",
        "2024-01-11",
        "2024-05-01",
        "2024-07-30",
        "2024-08-14",
        "2024-11-06",
        "2024-11-18",
        "2025-01-01",
        "2025-01-11",
        "2025-05-01",
        "2025-07-30",
        "2025-08-14",
        "2025-11-06",
        "2025-11-18",
        "2026-01-01",
        "2026-01-11",
        "2026-05-01",
    }
    ramadan_periods = [("2024-03-10", "2024-04-09"), ("2025-03-01", "2025-03-30"), ("2026-02-18", "2026-03-19")]
    df = pd.DataFrame(
        {
            "id_date": dates.strftime("%Y%m%d").astype(int),
            "date_complete": dates,
            "jour": dates.day,
            "mois": dates.month,
            "trimestre": dates.quarter,
            "annee": dates.year,
            "semaine": dates.isocalendar().week.astype(int),
            "libelle_jour": dates.strftime("%A"),
            "libelle_mois": dates.strftime("%B"),
            "est_weekend": dates.dayofweek >= 5,
            "est_ferie_maroc": dates.strftime("%Y-%m-%d").isin(feries_maroc),
        }
    )
    df["periode_ramadan"] = False
    for start, end in ramadan_periods:
        mask = (df["date_complete"] >= start) & (df["date_complete"] <= end)
        df.loc[mask, "periode_ramadan"] = True
    return df


def calculer_segments_clients(commandes: pd.DataFrame) -> pd.DataFrame:
    """Calculate Gold/Silver/Bronze segments from customer revenue."""
    commandes = commandes.copy()
    commandes["montant_ttc"] = commandes["quantite"].astype(float) * commandes["prix_unitaire"].astype(float)
    ca = commandes.groupby("id_client", as_index=False)["montant_ttc"].sum().rename(columns={"montant_ttc": "ca_total"})
    ca["segment_client"] = pd.cut(
        ca["ca_total"],
        bins=[-1, 4999.99, 14999.99, float("inf")],
        labels=["Bronze", "Silver", "Gold"],
    ).astype(str)
    return ca[["id_client", "segment_client", "ca_total"]]

