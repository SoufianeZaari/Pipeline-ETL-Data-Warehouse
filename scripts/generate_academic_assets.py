"""Generate academic files, diagrams and small PDFs for the Mexora report."""

from __future__ import annotations

import csv
import json
import random
import textwrap
from datetime import date, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


BASE_DIR = Path(__file__).resolve().parents[1]
ACADEMIC_RAW_DIR = BASE_DIR / "data" / "academic_raw"
GENERATED_DIR = BASE_DIR / "data" / "generated"
DOCS_DIR = BASE_DIR / "docs"
REPORT_ASSETS_DIR = BASE_DIR / "report" / "assets"
RANDOM_SEED = 20260530

REGIONS = [
    ("TNG", "Tanger", "Tanger-Assilah", "Tanger-Tétouan-Al Hoceïma", "Nord", 1275000, "90000"),
    ("TET", "Tétouan", "Tétouan", "Tanger-Tétouan-Al Hoceïma", "Nord", 380000, "93000"),
    ("CAS", "Casablanca", "Casablanca", "Casablanca-Settat", "Centre-Ouest", 3350000, "20000"),
    ("RBA", "Rabat", "Rabat", "Rabat-Salé-Kénitra", "Nord-Ouest", 580000, "10000"),
    ("FES", "Fès", "Fès", "Fès-Meknès", "Centre", 1200000, "30000"),
    ("MRK", "Marrakech", "Marrakech", "Marrakech-Safi", "Centre-Sud", 950000, "40000"),
    ("AGA", "Agadir", "Agadir-Ida Ou Tanane", "Souss-Massa", "Sud", 700000, "80000"),
    ("OUD", "Oujda", "Oujda-Angad", "Oriental", "Est", 500000, "60000"),
    ("AHO", "Al Hoceïma", "Al Hoceïma", "Tanger-Tétouan-Al Hoceïma", "Nord", 400000, "32000"),
    ("KEN", "Kénitra", "Kénitra", "Rabat-Salé-Kénitra", "Nord-Ouest", 430000, "14000"),
    ("MEK", "Meknès", "Meknès", "Fès-Meknès", "Centre", 630000, "50000"),
    ("NAD", "Nador", "Nador", "Oriental", "Nord-Est", 250000, "62000"),
]

CITY_VARIANTS = {"Tanger": ["Tanger", "tanger", "TANGER", "TNG", "Tnja", "Tangier"], "Casablanca": ["Casablanca", "casa", "CAS"], "Rabat": ["Rabat", "rabat", "RABAT"]}
STATUSES = ["livré", "annulé", "en_cours", "retourné", "OK", "KO", "DONE"]
PAYMENTS = ["Cash on Delivery", "Credit Card", "Bank Transfer", "Wallet"]
CANALS = ["Web", "Mobile", "Marketplace", "Social Ads", "Referral"]
ORIGINS = ["Maroc", "France", "Espagne", "USA", "Chine", "Turquie"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def mixed_date(value: date) -> str:
    return value.strftime(random.choice(["%d/%m/%Y", "%Y-%m-%d", "%b %d %Y"]))


def random_date(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))


def generate_regions() -> None:
    rows = [
        {"code_ville": c, "nom_ville_standard": v, "province": p, "region_admin": r, "zone_geo": z, "population": pop, "code_postal": cp}
        for c, v, p, r, z, pop, cp in REGIONS
    ]
    write_csv(ACADEMIC_RAW_DIR / "regions_maroc.csv", rows)


def generate_clients() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in read_csv(GENERATED_DIR / "customers.csv"):
        cid = int(row["customer_id"])
        parts = row["full_name"].split(" ", 1)
        email = row.get("email", "")
        if random.random() < 0.025:
            email = email.replace("@", "")
        if rows and random.random() < 0.03:
            email = str(random.choice(rows)["email"])
        birth = "2035-01-01" if random.random() < 0.01 else row.get("birth_date", "")
        rows.append(
            {
                "id_client": f"C{cid:05d}",
                "nom": parts[-1],
                "prenom": parts[0],
                "email": email,
                "date_naissance": birth,
                "sexe": random.choice([row.get("gender", ""), "m", "f", "1", "0", "Homme", "Femme"]),
                "ville": row.get("city", ""),
                "telephone": row.get("phone", ""),
                "date_inscription": row.get("registration_date", ""),
                "canal_acquisition": random.choice(CANALS),
            }
        )
    write_csv(ACADEMIC_RAW_DIR / "clients_mexora.csv", rows)
    return rows


def generate_produits() -> list[dict[str, object]]:
    produits: list[dict[str, object]] = []
    category_map = {"Electronics": "Electronique", "Fashion": "Mode", "Food": "Alimentation"}
    for row in read_csv(GENERATED_DIR / "products.csv"):
        category = category_map.get(row["category"], row["category"])
        if random.random() < 0.2:
            category = random.choice([category.lower(), category.upper(), category])
        price: object = None if random.random() < 0.03 else row.get("price", "")
        produits.append({"id_produit": f"P{int(row['product_id']):03d}", "nom": row["product_name"], "categorie": category, "sous_categorie": row["sub_category"], "marque": row["brand"], "fournisseur": row["supplier"], "prix_catalogue": price, "origine_pays": random.choice(ORIGINS), "date_creation": row["created_at"], "actif": False if random.random() < 0.06 else True})
    (ACADEMIC_RAW_DIR / "produits_mexora.json").write_text(json.dumps({"produits": produits}, ensure_ascii=False, indent=2), encoding="utf-8")
    return produits


def generate_commandes(clients: list[dict[str, object]], produits: list[dict[str, object]], n_rows: int = 50_000) -> None:
    rows: list[dict[str, object]] = []
    cities = [city for _, city, *_ in REGIONS]
    for index in range(1, n_rows + 1):
        duplicate = index > n_rows * 0.97 and rows
        order_id = random.choice(rows)["id_commande"] if duplicate else f"CMD{index:06d}"
        client, produit = random.choice(clients), random.choice(produits)
        order_date = random_date(date(2024, 1, 1), date(2026, 5, 20))
        delivery_date = order_date + timedelta(days=random.randint(1, 10))
        if random.random() < 0.005:
            delivery_date = order_date - timedelta(days=random.randint(1, 5))
        city = random.choice(cities)
        dirty_city = random.choice(CITY_VARIANTS.get(city, [city])) if random.random() < 0.35 else city
        quantity = -random.randint(1, 3) if random.random() < 0.008 else random.randint(1, 5)
        price = float(produit.get("prix_catalogue") or random.uniform(80, 9000))
        if random.random() < 0.01:
            price = 0
        rows.append({"id_commande": order_id, "id_client": client["id_client"], "id_produit": produit["id_produit"], "date_commande": mixed_date(order_date), "quantite": quantity, "prix_unitaire": round(price, 2), "statut": random.choice(STATUSES), "ville_livraison": dirty_city, "mode_paiement": random.choice(PAYMENTS), "id_livreur": "" if random.random() < 0.07 else f"L{random.randint(1, 5):03d}", "date_livraison": mixed_date(delivery_date)})
    write_csv(ACADEMIC_RAW_DIR / "commandes_mexora.csv", rows)


def generate_star_schema_png() -> None:
    REPORT_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(14, 9))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9)
    ax.axis("off")
    ax.set_title("Mexora - Schéma en étoile du Data Warehouse", fontsize=18, fontweight="bold")
    boxes = {
        "dim_customer\nclient, segment,\nville, région": (0.5, 6.5),
        "dim_product\nproduit, catégorie,\nmarque, fournisseur": (0.5, 3.5),
        "dim_date\njour, mois,\ntrimestre, Ramadan": (0.5, 0.8),
        "dim_region\nville, région,\npays": (10.5, 6.5),
        "dim_payment\nméthode,\nstatut paiement": (10.5, 3.5),
        "dim_delivery\ntransporteur,\nstatut livraison": (10.5, 0.8),
        "fact_sales\nGrain: ligne de commande\nMesures: quantité, CA,\nretour, remboursement,\ndélai livraison": (5.1, 3.3),
    }
    centers: dict[str, tuple[float, float]] = {}
    for label, (x, y) in boxes.items():
        fact = label.startswith("fact_sales")
        w, h = (3.7, 2.1) if fact else (2.9, 1.35)
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor="#0f766e" if fact else "#eef6ff", edgecolor="#134e4a" if fact else "#1d4ed8", linewidth=2))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=10, color="white" if fact else "#0f172a", fontweight="bold" if fact else "normal")
        centers[label.split("\n", 1)[0]] = (x + w / 2, y + h / 2)
    fact_center = centers["fact_sales"]
    for name, center in centers.items():
        if name != "fact_sales":
            ax.annotate("", xy=fact_center, xytext=center, arrowprops={"arrowstyle": "->", "color": "#475569", "lw": 1.5})
    fig.tight_layout()
    fig.savefig(REPORT_ASSETS_DIR / "schema_etoile_mexora.png", dpi=180)
    plt.close(fig)


def markdown_to_pdf(markdown_path: Path, pdf_path: Path, title: str) -> None:
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", fontSize=8.3, leading=10.5, spaceAfter=4))
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, rightMargin=1.6 * cm, leftMargin=1.6 * cm, topMargin=1.4 * cm, bottomMargin=1.4 * cm)
    story: list = [Paragraph(title, styles["Title"]), Spacer(1, 0.2 * cm)]
    table_buffer: list[list[str]] = []

    def flush_table() -> None:
        nonlocal table_buffer
        if len(table_buffer) >= 2:
            table = Table(table_buffer, repeatRows=1)
            table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 6.7), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
            story.extend([table, Spacer(1, 0.12 * cm)])
        table_buffer = []

    for raw in markdown_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            flush_table()
            story.append(Spacer(1, 0.06 * cm))
            continue
        if line.startswith("|") and line.endswith("|") and "---" not in line:
            table_buffer.append([cell.strip().replace("`", "") for cell in line.strip("|").split("|")])
            continue
        flush_table()
        if line.startswith("# "):
            story.append(Paragraph(line[2:], styles["Heading1"]))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:], styles["Heading2"]))
        elif line.startswith("### "):
            story.append(Paragraph(line[4:], styles["Heading3"]))
        elif line.startswith("- "):
            story.append(Paragraph("• " + line[2:].replace("`", ""), styles["Small"]))
        else:
            for chunk in textwrap.wrap(line.replace("`", ""), width=125) or [""]:
                story.append(Paragraph(chunk, styles["Small"]))
    flush_table()
    doc.build(story)


def main() -> None:
    random.seed(RANDOM_SEED)
    ACADEMIC_RAW_DIR.mkdir(parents=True, exist_ok=True)
    generate_regions()
    clients = generate_clients()
    produits = generate_produits()
    generate_commandes(clients, produits)
    generate_star_schema_png()
    markdown_to_pdf(DOCS_DIR / "modeling_justification.md", DOCS_DIR / "modeling_justification.pdf", "Mexora - Justification de modélisation")
    markdown_to_pdf(DOCS_DIR / "insights_metier.md", DOCS_DIR / "insights_metier.pdf", "Mexora - Insights métier")
    print("Livrables académiques générés.")


if __name__ == "__main__":
    main()
