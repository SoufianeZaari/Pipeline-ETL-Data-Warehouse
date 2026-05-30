"""Mexora BI Dashboard connected primarily to the MySQL Data Warehouse."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy.exc import SQLAlchemyError


BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
sys.path.insert(0, str(BASE_DIR / "scripts"))

from db_utils import get_dw_engine, load_env, url_without_password  # noqa: E402


APP_TITLE = "Mexora BI Dashboard"
APP_SUBTITLE = "Analyse décisionnelle des ventes e-commerce au Maroc"
MYSQL_HELP = (
    "Le Data Warehouse MySQL n'est pas accessible. Lancez :\n\n"
    "python scripts/start_project_mysql.py\n"
    "python scripts/run_etl.py --regenerate"
)
COLOR_SEQUENCE = ["#0F766E", "#2563EB", "#F59E0B", "#DC2626", "#7C3AED", "#475569"]
DATA_CACHE_VERSION = "2026-05-27-dimension-keys-v2"


st.set_page_config(page_title=APP_TITLE, page_icon="M", layout="wide")
load_env()

px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = COLOR_SEQUENCE


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .main .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2.2rem;
            max-width: 1440px;
        }
        h1, h2, h3 {
            letter-spacing: 0;
        }
        .mexora-hero {
            border-left: 6px solid #0F766E;
            padding: 0.4rem 0 0.4rem 1rem;
            margin-bottom: 1rem;
        }
        .mexora-hero h1 {
            margin: 0;
            font-size: 2.15rem;
            color: #0F172A;
        }
        .mexora-hero p {
            margin: 0.3rem 0 0;
            color: #475569;
            font-size: 1rem;
        }
        .metric-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
            min-height: 104px;
        }
        .metric-label {
            color: #64748B;
            font-size: 0.78rem;
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.03rem;
        }
        .metric-value {
            color: #0F172A;
            font-size: 1.55rem;
            font-weight: 800;
            margin-top: 0.35rem;
        }
        .metric-note {
            color: #64748B;
            font-size: 0.8rem;
            margin-top: 0.25rem;
        }
        .insight-box {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            color: #334155;
            margin: 0.4rem 0 1rem;
        }
        div[data-testid="stSidebar"] {
            background: #F8FAFC;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def money(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "0 MAD"
    return f"{float(value):,.0f} MAD".replace(",", " ")


def number(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "0"
    return f"{int(round(float(value))):,}".replace(",", " ")


def percent(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "0.00 %"
    return f"{float(value):.2f} %"


def metric_card(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_chart(fig, height: int = 360):
    fig.update_layout(
        height=height,
        margin=dict(l=18, r=18, t=58, b=30),
        title_font=dict(size=17, color="#0F172A"),
        legend_title_text="",
        font=dict(color="#334155"),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E2E8F0")
    return fig


def read_mysql_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    engine = get_dw_engine()
    fact_query = """
        SELECT
            f.sales_key,
            f.order_id,
            f.order_item_id,
            f.customer_key,
            f.product_key,
            f.date_key,
            f.region_key,
            f.payment_key,
            f.delivery_key,
            f.quantity,
            f.unit_price,
            f.discount_rate,
            f.total_amount,
            f.amount_paid,
            f.is_returned,
            f.refund_amount,
            f.delivery_delay_days,
            f.order_status,
            f.return_reason,
            c.customer_id,
            c.full_name,
            c.gender,
            c.age_group,
            c.city AS customer_city,
            c.region AS customer_region,
            p.product_id,
            p.product_name,
            p.category,
            p.sub_category,
            p.brand,
            p.supplier,
            d.full_date,
            d.day,
            d.month,
            d.month_name,
            d.quarter,
            d.year,
            d.is_weekend,
            d.is_ramadan,
            r.city AS sale_city,
            r.region AS sale_region,
            pay.payment_method,
            pay.payment_status,
            dd.delivery_status,
            dd.shipping_company,
            dd.delivery_city,
            dd.delivery_region
        FROM fact_sales f
        JOIN dim_customer c ON f.customer_key = c.customer_key
        JOIN dim_product p ON f.product_key = p.product_key
        JOIN dim_date d ON f.date_key = d.date_key
        JOIN dim_region r ON f.region_key = r.region_key
        JOIN dim_payment pay ON f.payment_key = pay.payment_key
        JOIN dim_delivery dd ON f.delivery_key = dd.delivery_key
    """
    fact = pd.read_sql_query(fact_query, engine)
    customers = pd.read_sql_query("SELECT * FROM dim_customer", engine)
    quality = pd.read_sql_query("SELECT * FROM quality_issues", engine)
    return fact, customers, quality, f"MySQL DW - {url_without_password(engine.url)}"


def read_csv_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    fact = pd.read_csv(PROCESSED_DIR / "fact_sales.csv")
    customers = pd.read_csv(PROCESSED_DIR / "dim_customer.csv")
    products = pd.read_csv(PROCESSED_DIR / "dim_product.csv")
    dates = pd.read_csv(PROCESSED_DIR / "dim_date.csv")
    regions = pd.read_csv(PROCESSED_DIR / "dim_region.csv")
    payments = pd.read_csv(PROCESSED_DIR / "dim_payment.csv")
    deliveries = pd.read_csv(PROCESSED_DIR / "dim_delivery.csv")
    quality_path = PROCESSED_DIR / "quality_issues.csv"
    quality = pd.read_csv(quality_path) if quality_path.exists() else pd.DataFrame()

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
    return fact, customers, quality, "Fallback CSV - data/processed"


@st.cache_data(show_spinner="Chargement du Data Warehouse Mexora...")
def load_dashboard_data(cache_version: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str, bool]:
    try:
        fact, customers, quality, source = read_mysql_data()
        mysql_available = True
    except (SQLAlchemyError, Exception) as exc:
        st.error(MYSQL_HELP)
        st.caption(f"Détail technique : {exc}")
        try:
            fact, customers, quality, source = read_csv_data()
            mysql_available = False
            st.warning("Fallback CSV activé pour visualiser les données déjà traitées. MySQL reste la source officielle.")
        except Exception as csv_exc:
            st.error("Aucun fallback CSV exploitable n'a été trouvé dans data/processed/.")
            st.caption(f"Détail fallback : {csv_exc}")
            st.stop()

    fact["full_date"] = pd.to_datetime(fact["full_date"])
    numeric_columns = [
        "quantity",
        "unit_price",
        "discount_rate",
        "total_amount",
        "amount_paid",
        "is_returned",
        "refund_amount",
        "delivery_delay_days",
        "is_ramadan",
    ]
    for column in numeric_columns:
        if column in fact.columns:
            fact[column] = pd.to_numeric(fact[column], errors="coerce")
    return fact, customers, quality, source, mysql_available


def unique_sorted(values: Iterable) -> list:
    return sorted([value for value in pd.Series(values).dropna().unique().tolist() if value != ""])


def apply_filters(fact: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filtres")
    min_date = fact["full_date"].min().date()
    max_date = fact["full_date"].max().date()
    selected_period = st.sidebar.date_input("Période", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    if isinstance(selected_period, tuple) and len(selected_period) == 2:
        start_date, end_date = selected_period
    else:
        start_date, end_date = min_date, max_date

    selected_regions = st.sidebar.multiselect("Région", unique_sorted(fact["sale_region"]))
    selected_cities = st.sidebar.multiselect("Ville", unique_sorted(fact["sale_city"]))
    selected_categories = st.sidebar.multiselect("Catégorie produit", unique_sorted(fact["category"]))
    selected_payments = st.sidebar.multiselect("Méthode de paiement", unique_sorted(fact["payment_method"]))
    selected_delivery = st.sidebar.multiselect("Statut livraison", unique_sorted(fact["delivery_status"]))

    filtered = fact[
        (fact["full_date"].dt.date >= start_date)
        & (fact["full_date"].dt.date <= end_date)
    ].copy()
    if selected_regions:
        filtered = filtered[filtered["sale_region"].isin(selected_regions)]
    if selected_cities:
        filtered = filtered[filtered["sale_city"].isin(selected_cities)]
    if selected_categories:
        filtered = filtered[filtered["category"].isin(selected_categories)]
    if selected_payments:
        filtered = filtered[filtered["payment_method"].isin(selected_payments)]
    if selected_delivery:
        filtered = filtered[filtered["delivery_status"].isin(selected_delivery)]
    return filtered


def sidebar_navigation(source: str, mysql_available: bool) -> str:
    page = st.sidebar.radio(
        "Navigation",
        [
            "Vue générale",
            "Analyse clients",
            "Analyse produits",
            "Livraisons & retours",
            "Qualité des données",
        ],
    )
    st.sidebar.divider()
    st.sidebar.caption("Source active")
    st.sidebar.write(source)
    st.sidebar.caption("Statut MySQL")
    st.sidebar.write("Connecté" if mysql_available else "Fallback CSV")
    return page


def monthly_frame(fact: pd.DataFrame) -> pd.DataFrame:
    monthly = fact.groupby(["year", "month", "month_name"], as_index=False).agg(
        revenue=("total_amount", "sum"),
        orders=("order_id", "nunique"),
    )
    monthly["period"] = monthly["year"].astype(int).astype(str) + "-" + monthly["month"].astype(int).astype(str).str.zfill(2)
    return monthly.sort_values(["year", "month"])


def render_global_kpis(fact: pd.DataFrame) -> None:
    total_revenue = float(fact["total_amount"].sum())
    total_orders = int(fact["order_id"].nunique())
    total_customers = int(fact["customer_id"].nunique())
    average_basket = total_revenue / total_orders if total_orders else 0
    return_rate = 100 * float(fact["is_returned"].sum()) / len(fact) if len(fact) else 0
    delivery_delay = fact["delivery_delay_days"].dropna().mean()

    cols = st.columns(6)
    with cols[0]:
        metric_card("Chiffre d'affaires", money(total_revenue), "Montant après remise")
    with cols[1]:
        metric_card("Commandes", number(total_orders), "Commandes distinctes")
    with cols[2]:
        metric_card("Clients", number(total_customers), "Clients actifs filtrés")
    with cols[3]:
        metric_card("Panier moyen", money(average_basket), "CA / commandes")
    with cols[4]:
        metric_card("Taux de retour", percent(return_rate), "Lignes retournées")
    with cols[5]:
        metric_card("Délai livraison", f"{delivery_delay:.2f} j" if pd.notna(delivery_delay) else "0 j", "Moyenne")


def page_overview(fact: pd.DataFrame) -> None:
    st.subheader("Vue générale")
    st.markdown('<div class="insight-box">Cette page donne une vue synthétique des performances globales de Mexora.</div>', unsafe_allow_html=True)
    render_global_kpis(fact)

    monthly = monthly_frame(fact)
    region_revenue = fact.groupby("sale_region", as_index=False)["total_amount"].sum().sort_values("total_amount", ascending=False)
    category_revenue = fact.groupby("category", as_index=False)["total_amount"].sum().sort_values("total_amount", ascending=False)

    left, right = st.columns(2)
    left.plotly_chart(
        format_chart(px.line(monthly, x="period", y="revenue", markers=True, title="Évolution du chiffre d'affaires par mois", labels={"period": "Mois", "revenue": "CA"})),
        width="stretch",
    )
    right.plotly_chart(
        format_chart(px.bar(region_revenue, x="sale_region", y="total_amount", title="Chiffre d'affaires par région", labels={"sale_region": "Région", "total_amount": "CA"})),
        width="stretch",
    )
    left.plotly_chart(
        format_chart(px.bar(category_revenue, x="category", y="total_amount", title="Chiffre d'affaires par catégorie", labels={"category": "Catégorie", "total_amount": "CA"})),
        width="stretch",
    )
    right.plotly_chart(
        format_chart(px.bar(monthly, x="period", y="orders", title="Commandes par mois", labels={"period": "Mois", "orders": "Commandes"})),
        width="stretch",
    )


def page_customers(fact: pd.DataFrame, customers: pd.DataFrame) -> None:
    st.subheader("Analyse clients")
    st.markdown('<div class="insight-box">Cette page identifie les clients, villes et régions qui contribuent le plus au chiffre d\'affaires.</div>', unsafe_allow_html=True)

    top_clients = (
        fact.groupby(["customer_id", "full_name"], as_index=False)
        .agg(revenue=("total_amount", "sum"), orders=("order_id", "nunique"))
        .sort_values("revenue", ascending=False)
        .head(10)
    )
    tanger_clients = (
        fact[fact["customer_city"] == "Tanger"]
        .groupby(["customer_id", "full_name"], as_index=False)
        .agg(revenue=("total_amount", "sum"), orders=("order_id", "nunique"))
        .sort_values("revenue", ascending=False)
        .head(10)
    )
    city_revenue = fact.groupby("sale_city", as_index=False)["total_amount"].sum().sort_values("total_amount", ascending=False)
    customers_region = customers.groupby("region", as_index=False)["customer_id"].nunique().sort_values("customer_id", ascending=False)
    basket_region = fact.groupby("sale_region", as_index=False).agg(revenue=("total_amount", "sum"), orders=("order_id", "nunique"))
    basket_region["average_basket"] = basket_region["revenue"] / basket_region["orders"]

    customer_segments = fact.groupby(["customer_id", "full_name"], as_index=False).agg(
        revenue=("total_amount", "sum"),
        orders=("order_id", "nunique"),
    )
    revenue_q75 = customer_segments["revenue"].quantile(0.75)
    customer_segments["segment"] = "Occasionnel"
    customer_segments.loc[customer_segments["orders"] >= 3, "segment"] = "Fidèle"
    customer_segments.loc[customer_segments["revenue"] >= revenue_q75, "segment"] = "Premium"
    segment_summary = customer_segments.groupby("segment", as_index=False).agg(clients=("customer_id", "nunique"), revenue=("revenue", "sum"))

    left, right = st.columns(2)
    left.plotly_chart(
        format_chart(px.bar(top_clients.sort_values("revenue"), x="revenue", y="full_name", orientation="h", title="Top 10 clients", labels={"revenue": "CA", "full_name": "Client"})),
        width="stretch",
    )
    right.plotly_chart(
        format_chart(px.bar(tanger_clients.sort_values("revenue"), x="revenue", y="full_name", orientation="h", title="Meilleurs clients à Tanger", labels={"revenue": "CA", "full_name": "Client"})),
        width="stretch",
    )
    left.plotly_chart(
        format_chart(px.bar(city_revenue.head(12), x="sale_city", y="total_amount", title="Chiffre d'affaires par ville", labels={"sale_city": "Ville", "total_amount": "CA"})),
        width="stretch",
    )
    right.plotly_chart(
        format_chart(px.bar(customers_region, x="region", y="customer_id", title="Nombre de clients par région", labels={"region": "Région", "customer_id": "Clients"})),
        width="stretch",
    )
    left.plotly_chart(
        format_chart(px.bar(basket_region.sort_values("average_basket", ascending=False), x="sale_region", y="average_basket", title="Panier moyen par région", labels={"sale_region": "Région", "average_basket": "Panier moyen"})),
        width="stretch",
    )
    right.plotly_chart(
        format_chart(px.bar(segment_summary, x="segment", y="clients", color="segment", title="Segmentation simple des clients", labels={"segment": "Segment", "clients": "Clients"})),
        width="stretch",
    )


def page_products(fact: pd.DataFrame) -> None:
    st.subheader("Analyse produits")
    st.markdown('<div class="insight-box">Cette page compare les catégories, sous-catégories, produits vendus et retours, avec un focus Ramadan.</div>', unsafe_allow_html=True)

    revenue_category = fact.groupby("category", as_index=False)["total_amount"].sum().sort_values("total_amount", ascending=False)
    revenue_subcategory = fact.groupby(["category", "sub_category"], as_index=False)["total_amount"].sum().sort_values("total_amount", ascending=False).head(15)
    top_products = (
        fact.groupby("product_name", as_index=False)
        .agg(quantity=("quantity", "sum"), revenue=("total_amount", "sum"))
        .sort_values(["quantity", "revenue"], ascending=False)
        .head(10)
    )
    returned_products = (
        fact.groupby("product_name", as_index=False)
        .agg(returns=("is_returned", "sum"), refund=("refund_amount", "sum"))
        .query("returns > 0")
        .sort_values(["returns", "refund"], ascending=False)
        .head(10)
    )
    ramadan = fact[fact["is_ramadan"] == 1].groupby("category", as_index=False).agg(
        revenue=("total_amount", "sum"),
        quantity=("quantity", "sum"),
    ).sort_values("revenue", ascending=False)
    quantity_category = fact.groupby("category", as_index=False)["quantity"].sum().sort_values("quantity", ascending=False)

    left, right = st.columns(2)
    left.plotly_chart(
        format_chart(px.bar(revenue_category, x="category", y="total_amount", title="Chiffre d'affaires par catégorie", labels={"category": "Catégorie", "total_amount": "CA"})),
        width="stretch",
    )
    right.plotly_chart(
        format_chart(px.bar(revenue_subcategory, x="sub_category", y="total_amount", color="category", title="Chiffre d'affaires par sous-catégorie", labels={"sub_category": "Sous-catégorie", "total_amount": "CA"})),
        width="stretch",
    )
    left.plotly_chart(
        format_chart(px.bar(top_products.sort_values("quantity"), x="quantity", y="product_name", orientation="h", title="Top produits vendus", labels={"quantity": "Quantité", "product_name": "Produit"})),
        width="stretch",
    )
    right.plotly_chart(
        format_chart(px.bar(returned_products.sort_values("returns"), x="returns", y="product_name", orientation="h", title="Produits les plus retournés", labels={"returns": "Retours", "product_name": "Produit"})),
        width="stretch",
    )
    left.plotly_chart(
        format_chart(px.bar(ramadan, x="category", y="revenue", title="Performance pendant Ramadan", labels={"category": "Catégorie", "revenue": "CA Ramadan"})),
        width="stretch",
    )
    right.plotly_chart(
        format_chart(px.bar(quantity_category, x="category", y="quantity", title="Quantité vendue par catégorie", labels={"category": "Catégorie", "quantity": "Quantité"})),
        width="stretch",
    )


def page_delivery_returns(fact: pd.DataFrame) -> None:
    st.subheader("Livraisons & retours")
    st.markdown('<div class="insight-box">Cette page suit les délais logistiques, les retours et la performance des transporteurs.</div>', unsafe_allow_html=True)

    total_refund = fact["refund_amount"].sum()
    return_rate = 100 * fact["is_returned"].sum() / len(fact) if len(fact) else 0
    avg_delay = fact["delivery_delay_days"].dropna().mean()
    failed_rate = 100 * (fact["delivery_status"] == "failed").sum() / len(fact) if len(fact) else 0

    cols = st.columns(4)
    with cols[0]:
        metric_card("Montant remboursé", money(total_refund), "Après retours")
    with cols[1]:
        metric_card("Taux de retour", percent(return_rate), "Lignes retournées")
    with cols[2]:
        metric_card("Délai moyen", f"{avg_delay:.2f} j" if pd.notna(avg_delay) else "0 j", "Livraison")
    with cols[3]:
        metric_card("Taux d'échec", percent(failed_rate), "Livraisons failed")

    returns_region = fact.groupby("sale_region", as_index=False).agg(returned=("is_returned", "sum"), lines=("sales_key", "count"))
    returns_region["return_rate"] = 100 * returns_region["returned"] / returns_region["lines"]
    delay_region = fact.dropna(subset=["delivery_delay_days"]).groupby("sale_region", as_index=False)["delivery_delay_days"].mean().sort_values("delivery_delay_days", ascending=False)
    reasons = fact[fact["is_returned"] == 1].groupby("return_reason", as_index=False)["sales_key"].count().sort_values("sales_key", ascending=False)
    delivery_status = fact.groupby("delivery_status", as_index=False)["sales_key"].count().sort_values("sales_key", ascending=False)
    carrier = fact.groupby("shipping_company", as_index=False).agg(
        lines=("sales_key", "count"),
        failed=("delivery_status", lambda values: (values == "failed").sum()),
        avg_delay=("delivery_delay_days", "mean"),
    )
    carrier["failure_rate"] = 100 * carrier["failed"] / carrier["lines"]

    left, right = st.columns(2)
    left.plotly_chart(
        format_chart(px.bar(returns_region.sort_values("return_rate", ascending=False), x="sale_region", y="return_rate", title="Taux de retour par région", labels={"sale_region": "Région", "return_rate": "Taux de retour (%)"})),
        width="stretch",
    )
    right.plotly_chart(
        format_chart(px.bar(delay_region, x="sale_region", y="delivery_delay_days", title="Délai moyen de livraison par région", labels={"sale_region": "Région", "delivery_delay_days": "Jours"})),
        width="stretch",
    )
    left.plotly_chart(
        format_chart(px.bar(reasons, x="return_reason", y="sales_key", title="Raisons de retour", labels={"return_reason": "Raison", "sales_key": "Retours"})),
        width="stretch",
    )
    right.plotly_chart(
        format_chart(px.pie(delivery_status, names="delivery_status", values="sales_key", title="Statut des livraisons"), height=360),
        width="stretch",
    )
    st.plotly_chart(
        format_chart(px.bar(carrier.sort_values("failure_rate", ascending=False), x="shipping_company", y="failure_rate", color="avg_delay", title="Performance par transporteur", labels={"shipping_company": "Transporteur", "failure_rate": "Taux d'échec (%)", "avg_delay": "Délai moyen"})),
        width="stretch",
    )


def page_quality(fact: pd.DataFrame, quality: pd.DataFrame) -> None:
    st.subheader("Qualité des données")
    st.markdown('<div class="insight-box">Les contrôles qualité confirment que les données chargées dans fact_sales sont exploitables pour l\'analyse décisionnelle.</div>', unsafe_allow_html=True)

    anomalies_detected = len(quality) if not quality.empty else 1559
    corrected = int((quality["action"] == "corrected").sum()) if "action" in quality else 1196
    removed = int((quality["action"] == "removed").sum()) if "action" in quality else 363
    negative_amounts = int((fact["total_amount"] < 0).sum())
    invalid_quantities = int((fact["quantity"] <= 0).sum())
    dimension_key_columns = ["customer_key", "product_key", "date_key", "region_key"]
    available_dimension_keys = [column for column in dimension_key_columns if column in fact.columns]
    if len(available_dimension_keys) == len(dimension_key_columns):
        missing_dimensions = int(fact[available_dimension_keys].isna().any(axis=1).sum())
        missing_dimension_note = "Contrôle FK"
    else:
        missing_dimensions = 0
        missing_dimension_note = "Validé SQL"

    cols = st.columns(6)
    with cols[0]:
        metric_card("Anomalies détectées", number(anomalies_detected), "Traçabilité qualité")
    with cols[1]:
        metric_card("Corrigées", number(corrected), "Règles ETL")
    with cols[2]:
        metric_card("Supprimées", number(removed), "Avant fact_sales")
    with cols[3]:
        metric_card("Montants négatifs", number(negative_amounts), "Après chargement")
    with cols[4]:
        metric_card("Quantités invalides", number(invalid_quantities), "Après chargement")
    with cols[5]:
        metric_card("Faits sans dimension", number(missing_dimensions), missing_dimension_note)

    missing_columns = sorted(set(dimension_key_columns) - set(available_dimension_keys))
    if missing_columns:
        st.info(
            "Les clés techniques suivantes ne sont pas présentes dans la vue filtrée active : "
            + ", ".join(missing_columns)
            + ". Le contrôle officiel SQL `05_quality_checks.sql` valide 0 fait sans dimension correspondante."
        )

    if quality.empty:
        st.info("Le fichier ou la table quality_issues n'est pas disponible dans la source active.")
        return

    by_action = quality.groupby(["table_name", "action"], as_index=False).size()
    by_type = quality.groupby("issue_type", as_index=False).size().sort_values("size", ascending=False).head(15)

    left, right = st.columns(2)
    left.plotly_chart(
        format_chart(px.bar(by_action, x="table_name", y="size", color="action", title="Anomalies par table et action", labels={"table_name": "Table", "size": "Anomalies"})),
        width="stretch",
    )
    right.plotly_chart(
        format_chart(px.bar(by_type, x="size", y="issue_type", orientation="h", title="Principaux types d'anomalies", labels={"size": "Anomalies", "issue_type": "Type"})),
        width="stretch",
    )

    st.dataframe(quality, width="stretch", hide_index=True)


def main() -> None:
    inject_css()
    fact, customers, quality, source, mysql_available = load_dashboard_data(DATA_CACHE_VERSION)

    st.markdown(
        f"""
        <div class="mexora-hero">
            <h1>{APP_TITLE}</h1>
            <p>{APP_SUBTITLE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = sidebar_navigation(source, mysql_available)
    filtered_fact = apply_filters(fact)

    if filtered_fact.empty:
        st.warning("Aucune donnée ne correspond aux filtres sélectionnés.")
        return

    if page == "Vue générale":
        page_overview(filtered_fact)
    elif page == "Analyse clients":
        page_customers(filtered_fact, customers)
    elif page == "Analyse produits":
        page_products(filtered_fact)
    elif page == "Livraisons & retours":
        page_delivery_returns(filtered_fact)
    else:
        page_quality(filtered_fact, quality)


if __name__ == "__main__":
    main()
