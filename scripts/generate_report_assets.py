"""Generate static report figures from processed Mexora warehouse CSV files."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
ASSETS_DIR = BASE_DIR / "report" / "assets"


def load_fact() -> tuple[pd.DataFrame, pd.DataFrame]:
    fact = pd.read_csv(PROCESSED_DIR / "fact_sales.csv")
    customers = pd.read_csv(PROCESSED_DIR / "dim_customer.csv")
    products = pd.read_csv(PROCESSED_DIR / "dim_product.csv")
    dates = pd.read_csv(PROCESSED_DIR / "dim_date.csv")
    regions = pd.read_csv(PROCESSED_DIR / "dim_region.csv")
    payments = pd.read_csv(PROCESSED_DIR / "dim_payment.csv")
    deliveries = pd.read_csv(PROCESSED_DIR / "dim_delivery.csv")
    quality = pd.read_csv(PROCESSED_DIR / "quality_issues.csv")

    fact = (
        fact.merge(customers, on="customer_key", how="left")
        .merge(products, on="product_key", how="left")
        .merge(dates, on="date_key", how="left")
        .merge(regions, on="region_key", how="left", suffixes=("", "_sale"))
        .merge(payments, on="payment_key", how="left")
        .merge(deliveries, on="delivery_key", how="left")
    )
    fact = fact.rename(
        columns={
            "city": "customer_city",
            "region": "customer_region",
            "city_sale": "sale_city",
            "region_sale": "sale_region",
        }
    )
    return fact, quality


def save_figure(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()


def overview(fact: pd.DataFrame) -> None:
    monthly = fact.groupby(["year", "month"], as_index=False)["total_amount"].sum()
    monthly["period"] = monthly["year"].astype(str) + "-" + monthly["month"].astype(str).str.zfill(2)
    region = fact.groupby("sale_region")["total_amount"].sum().sort_values(ascending=False).head(8)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].plot(monthly["period"], monthly["total_amount"], color="#0F766E", linewidth=2.4)
    axes[0].set_title("Chiffre d'affaires mensuel")
    axes[0].tick_params(axis="x", rotation=60, labelsize=8)
    axes[0].set_ylabel("MAD")
    region.sort_values().plot(kind="barh", ax=axes[1], color="#2563EB")
    axes[1].set_title("CA par région")
    axes[1].set_xlabel("MAD")
    save_figure(ASSETS_DIR / "dashboard_vue_generale.png")


def clients(fact: pd.DataFrame) -> None:
    top_clients = fact.groupby("full_name")["total_amount"].sum().sort_values(ascending=False).head(10)
    city = fact.groupby("sale_city")["total_amount"].sum().sort_values(ascending=False).head(10)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    top_clients.sort_values().plot(kind="barh", ax=axes[0], color="#0F766E")
    axes[0].set_title("Top 10 clients")
    city.plot(kind="bar", ax=axes[1], color="#F59E0B")
    axes[1].set_title("CA par ville")
    axes[1].tick_params(axis="x", rotation=45)
    save_figure(ASSETS_DIR / "dashboard_analyse_clients.png")


def products(fact: pd.DataFrame) -> None:
    category = fact.groupby("category")["total_amount"].sum().sort_values(ascending=False)
    ramadan = fact[fact["is_ramadan"] == 1].groupby("category")["total_amount"].sum().sort_values(ascending=False)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    category.plot(kind="bar", ax=axes[0], color="#2563EB")
    axes[0].set_title("CA par catégorie")
    axes[0].tick_params(axis="x", rotation=0)
    ramadan.plot(kind="bar", ax=axes[1], color="#7C3AED")
    axes[1].set_title("Performance pendant Ramadan")
    axes[1].tick_params(axis="x", rotation=0)
    save_figure(ASSETS_DIR / "dashboard_analyse_produits.png")


def delivery_returns(fact: pd.DataFrame) -> None:
    returns = fact.groupby("sale_region")["is_returned"].mean().sort_values(ascending=False) * 100
    delay = fact.groupby("sale_region")["delivery_delay_days"].mean().sort_values(ascending=False)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    returns.sort_values().plot(kind="barh", ax=axes[0], color="#DC2626")
    axes[0].set_title("Taux de retour par région")
    axes[0].set_xlabel("%")
    delay.sort_values().plot(kind="barh", ax=axes[1], color="#0F766E")
    axes[1].set_title("Délai moyen livraison")
    axes[1].set_xlabel("jours")
    save_figure(ASSETS_DIR / "dashboard_livraisons_retours.png")


def quality(quality_issues: pd.DataFrame) -> None:
    by_action = quality_issues.groupby(["table_name", "action"]).size().unstack(fill_value=0)
    by_type = quality_issues.groupby("issue_type").size().sort_values(ascending=False).head(10)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    by_action.plot(kind="bar", stacked=True, ax=axes[0], color=["#0F766E", "#DC2626"])
    axes[0].set_title("Anomalies par table et action")
    axes[0].tick_params(axis="x", rotation=45)
    by_type.sort_values().plot(kind="barh", ax=axes[1], color="#F59E0B")
    axes[1].set_title("Types d'anomalies")
    save_figure(ASSETS_DIR / "dashboard_qualite_donnees.png")


def main() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    fact, quality_issues = load_fact()
    overview(fact)
    clients(fact)
    products(fact)
    delivery_returns(fact)
    quality(quality_issues)
    print(f"Figures générées dans {ASSETS_DIR}")


if __name__ == "__main__":
    main()
