"""Build academic dimensions and fact table from cleaned DataFrames."""

from __future__ import annotations

import logging
from datetime import date

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


# ---------------------------------------------------------------------------
# Livreur metadata (L001–L005 present in commandes_mexora.csv + unknown)
# ---------------------------------------------------------------------------
_LIVREUR_META: dict[str, dict[str, str]] = {
    "L001": {"nom_livreur": "Amira Benali", "type_transport": "Moto", "zone_couverture": "Tanger"},
    "L002": {"nom_livreur": "Youssef Chraibi", "type_transport": "Camionnette", "zone_couverture": "Casablanca"},
    "L003": {"nom_livreur": "Salma Idrissi", "type_transport": "Moto", "zone_couverture": "Rabat"},
    "L004": {"nom_livreur": "Omar Tahiri", "type_transport": "Vélo", "zone_couverture": "Marrakech"},
    "L005": {"nom_livreur": "Nadia Fassi", "type_transport": "Camionnette", "zone_couverture": "Fès"},
    "-1":   {"nom_livreur": "Livreur inconnu", "type_transport": "Inconnu", "zone_couverture": "Inconnue"},
}


def build_dim_livreur(df_commandes: pd.DataFrame) -> pd.DataFrame:
    """Build DIM_LIVREUR from unique carrier IDs in cleaned commandes."""
    ids = df_commandes["id_livreur"].dropna().astype(str).str.strip().unique().tolist()
    if "-1" not in ids:
        ids = ["-1"] + ids
    rows = []
    for sk, nk in enumerate(ids, start=1):
        meta = _LIVREUR_META.get(nk, {"nom_livreur": f"Livreur {nk}", "type_transport": "Inconnu", "zone_couverture": "Inconnue"})
        rows.append({"id_livreur": sk, "id_livreur_nk": nk, **meta})
    df = pd.DataFrame(rows)
    logging.info("[BUILD] dim_livreur: %s lignes", len(df))
    return df


def build_dim_region(df_regions: pd.DataFrame) -> pd.DataFrame:
    """Build DIM_REGION from the clean geographic reference file."""
    df = df_regions.copy()
    df = df.rename(columns={
        "nom_ville_standard": "ville",
        "region_admin": "region_admin",
        "province": "province",
        "zone_geo": "zone_geo",
    })
    df = df[["ville", "province", "region_admin", "zone_geo"]].drop_duplicates(subset=["ville"]).reset_index(drop=True)
    df.insert(0, "id_region", range(1, len(df) + 1))
    df["pays"] = "Maroc"
    logging.info("[BUILD] dim_region: %s lignes", len(df))
    return df


def build_dim_produit(df_produits: pd.DataFrame) -> pd.DataFrame:
    """Build DIM_PRODUIT (SCD Type 2 ready) from cleaned products DataFrame."""
    df = df_produits.copy()
    df = df.rename(columns={
        "id_produit": "id_produit_nk",
        "nom": "nom_produit",
        "sous_categorie": "sous_categorie",
        "marque": "marque",
        "fournisseur": "fournisseur",
        "prix_catalogue": "prix_standard",
        "origine_pays": "origine_pays",
    })
    cols = ["id_produit_nk", "nom_produit", "categorie", "sous_categorie", "marque",
            "fournisseur", "prix_standard", "origine_pays", "date_debut", "date_fin", "est_actif"]
    for col in cols:
        if col not in df.columns:
            df[col] = None
    df = df[cols].reset_index(drop=True)
    df["est_actif"] = df["est_actif"].astype(bool)  # int → bool for PostgreSQL BOOLEAN
    df.insert(0, "id_produit_sk", range(1, len(df) + 1))
    logging.info("[BUILD] dim_produit: %s lignes", len(df))
    return df


def build_dim_client(df_clients: pd.DataFrame, df_commandes: pd.DataFrame,
                     df_regions: pd.DataFrame) -> pd.DataFrame:
    """Build DIM_CLIENT with segments and SCD Type 2 columns."""
    segments = calculer_segments_clients(df_commandes)
    # Build city → region_admin lookup from reference
    region_lookup = (
        df_regions[["nom_ville_standard", "region_admin"]]
        .drop_duplicates("nom_ville_standard")
        .rename(columns={"nom_ville_standard": "ville"})
        .set_index("ville")["region_admin"]
        .to_dict()
    )

    df = df_clients.copy()
    df["nom_complet"] = (df["prenom"].fillna("") + " " + df["nom"].fillna("")).str.strip()
    df = df.merge(segments[["id_client", "segment_client"]], on="id_client", how="left")
    df["segment_client"] = df["segment_client"].fillna("Bronze")
    df["region_admin"] = df["ville"].map(region_lookup).fillna("Inconnue")
    # CHAR(1) constraint in PostgreSQL: normalize sexe to single character
    df["sexe"] = df["sexe"].fillna("?").str[:1].replace({"i": "?"})  # 'inconnu' → '?'

    today_str = str(date.today())
    df["date_debut"] = today_str
    df["date_fin"] = "9999-12-31"
    df["est_actif"] = True

    cols = ["id_client", "nom_complet", "tranche_age", "sexe", "ville",
            "region_admin", "segment_client", "canal_acquisition",
            "date_debut", "date_fin", "est_actif"]
    for col in cols:
        if col not in df.columns:
            df[col] = None
    df = df[cols].rename(columns={"id_client": "id_client_nk"}).reset_index(drop=True)
    df.insert(0, "id_client_sk", range(1, len(df) + 1))
    logging.info("[BUILD] dim_client: %s lignes", len(df))
    return df


def build_fait_ventes(
    df_commandes: pd.DataFrame,
    dim_temps: pd.DataFrame,
    dim_client: pd.DataFrame,
    dim_produit: pd.DataFrame,
    dim_region: pd.DataFrame,
    dim_livreur: pd.DataFrame,
) -> pd.DataFrame:
    """Build FAIT_VENTES by joining cleaned commandes with dimension surrogate keys."""
    df = df_commandes.copy()

    # Surrogate key lookups
    valid_dates = set(dim_temps["id_date"].astype(int))
    sk_client = dim_client.set_index("id_client_nk")["id_client_sk"].to_dict()
    sk_produit = dim_produit.set_index("id_produit_nk")["id_produit_sk"].to_dict()
    sk_region = dim_region.set_index("ville")["id_region"].to_dict()
    sk_livreur = dim_livreur.set_index("id_livreur_nk")["id_livreur"].to_dict()

    df["id_date"] = df["date_commande"].dt.strftime("%Y%m%d").astype(int)
    # Keep only dates that exist in dim_temps
    df = df[df["id_date"].isin(valid_dates)]
    df["id_client"] = df["id_client"].astype(str).map(sk_client)
    df["id_produit"] = df["id_produit"].astype(str).map(sk_produit)
    df["id_region"] = df["ville_livraison"].map(sk_region)
    df["id_livreur"] = df["id_livreur"].astype(str).map(sk_livreur)

    df["quantite_vendue"] = df["quantite"].astype(float).astype(int)
    df["montant_ht"] = (df["quantite"].astype(float) * df["prix_unitaire"].astype(float)).round(2)
    df["montant_ttc"] = (df["montant_ht"] * 1.20).round(2)  # TVA 20% Maroc
    df["remise_pct"] = 0.0

    df["date_livraison_parsed"] = pd.to_datetime(df["date_livraison"], format="mixed", dayfirst=True, errors="coerce")
    df["delai_livraison_jours"] = (
        (df["date_livraison_parsed"] - df["date_commande"]).dt.days
        .clip(lower=0)
        .astype("Int64")
    )

    df["statut_commande"] = df["statut"]

    # Drop rows without mandatory FK or with unrecognized status (violates CHECK constraint)
    before = len(df)
    valid_statuts = {"livré", "annulé", "en_cours", "retourné"}
    df = df[df["statut_commande"].isin(valid_statuts)]
    df = df.dropna(subset=["id_date", "id_client", "id_produit"])
    logging.info("[BUILD] fait_ventes: %s lignes supprimées (FK manquantes)", before - len(df))

    fact_cols = ["id_commande", "id_date", "id_produit", "id_client", "id_region", "id_livreur",
                 "quantite_vendue", "montant_ht", "montant_ttc", "delai_livraison_jours",
                 "remise_pct", "statut_commande"]
    df = df[fact_cols].reset_index(drop=True)
    logging.info("[BUILD] fait_ventes: %s lignes produites", len(df))
    return df

