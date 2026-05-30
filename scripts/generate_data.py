"""Generate realistic but intentionally imperfect Mexora OLTP data."""

from __future__ import annotations

import csv
import argparse
import random
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from db_utils import BASE_DIR, get_oltp_engine, quote_identifier, run_sql_file


GENERATED_DIR = BASE_DIR / "data" / "generated"
OLTP_SCHEMA = BASE_DIR / "sql" / "01_oltp_schema.sql"

RANDOM_SEED = 20260526

CITY_REGION = {
    "Tanger": "Tanger-Tétouan-Al Hoceïma",
    "Tétouan": "Tanger-Tétouan-Al Hoceïma",
    "Casablanca": "Casablanca-Settat",
    "Rabat": "Rabat-Salé-Kénitra",
    "Fès": "Fès-Meknès",
    "Marrakech": "Marrakech-Safi",
    "Agadir": "Souss-Massa",
    "Oujda": "Oriental",
    "Al Hoceïma": "Tanger-Tétouan-Al Hoceïma",
    "Kénitra": "Rabat-Salé-Kénitra",
    "Meknès": "Fès-Meknès",
    "Nador": "Oriental",
}

CITY_VARIANTS = {
    "Tanger": ["Tanger", "tanger", "TANGER", "Tangier", "TNG", "Tnja"],
    "Casablanca": ["Casablanca", "casa", "CASABLANCA", "CAS"],
    "Rabat": ["Rabat", "rabat", "RABAT"],
    "Tétouan": ["Tétouan", "Tetouan", "TETOUAN"],
    "Al Hoceïma": ["Al Hoceïma", "Al Hoceima", "AL HOCEIMA"],
}

REGION_VARIANTS = {
    "Tanger-Tétouan-Al Hoceïma": [
        "Tanger-Tétouan-Al Hoceïma",
        "Tanger-Tétouan-Al Hoceima",
        "Tanger Tetouan",
        "TTA",
    ],
    "Casablanca-Settat": ["Casablanca-Settat", "Casa Settat", "CASA-SETTAT"],
    "Rabat-Salé-Kénitra": ["Rabat-Salé-Kénitra", "Rabat Sale Kenitra", "RSK"],
    "Fès-Meknès": ["Fès-Meknès", "Fes Meknes"],
}

PRODUCT_CATALOG = {
    "Electronics": {
        "Smartphones": (1200, 9000),
        "Laptops": (3500, 18000),
        "Headphones": (150, 2200),
        "Smart Watches": (400, 4500),
        "Accessories": (50, 1200),
    },
    "Fashion": {
        "Shoes": (180, 1600),
        "T-Shirts": (80, 500),
        "Jackets": (250, 1800),
        "Bags": (120, 1300),
        "Traditional Clothes": (250, 2500),
    },
    "Food": {
        "Dates": (45, 240),
        "Olive Oil": (60, 500),
        "Tea": (30, 220),
        "Spices": (20, 160),
        "Biscuits": (12, 90),
        "Canned Food": (15, 120),
    },
}

BRANDS = {
    "Electronics": ["AtlasTech", "DigiNord", "CasaMobile", "MedConnect"],
    "Fashion": ["MedinaWear", "TanjaStyle", "UrbanSouk", "Nakhil"],
    "Food": ["SaharaTaste", "AgriMaroc", "RifBio", "AtlasGourmet"],
}

SUPPLIERS = ["Tanger Supply", "Maroc Distribution", "Atlas Wholesale", "MediSupplier"]
FIRST_NAMES = ["Sara", "Yassine", "Imane", "Omar", "Nadia", "Mehdi", "Salma", "Amine", "Hajar", "Karim"]
LAST_NAMES = ["El Amrani", "Bennani", "Tahiri", "Alaoui", "Mansouri", "Rifi", "Berrada", "Fassi", "Tazi", "Ziani"]
PAYMENT_METHODS = ["Cash on Delivery", "Credit Card", "Bank Transfer", "Wallet"]
ORDER_STATUSES = ["completed", "cancelled", "pending", "returned", "done", "ok", "return", "cancel", "DONE", "OK", "Annulé"]
DELIVERY_STATUSES = ["delivered", "in_transit", "delayed", "failed", "livré", "Livré", "DELIVERED", "KO"]
PAYMENT_STATUSES = ["paid", "pending", "failed", "unknown", "", "ok", "done", "KO"]
SHIPPING_COMPANIES = ["Amana Express", "Barid Logistics", "Jibli", "Tanger Delivery", "AtlasShip"]
RETURN_REASONS = ["Damaged product", "Wrong item", "Late delivery", "Customer changed mind", "Quality issue"]


def mixed_date(value: date | None) -> str:
    """Return a date as one of several formats to simulate dirty sources."""
    if value is None:
        return ""
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%b %d %Y"]
    return value.strftime(random.choice(formats))


def parse_date_for_mysql(value: Any) -> str | None:
    text_value = str(value or "").strip()
    if not text_value:
        return None
    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%b %d %Y"]:
        try:
            return datetime.strptime(text_value, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def choose_dirty_city(city: str) -> str:
    if random.random() < 0.04:
        return ""
    if city in CITY_VARIANTS and random.random() < 0.35:
        return random.choice(CITY_VARIANTS[city])
    return city


def choose_dirty_region(region: str) -> str:
    if random.random() < 0.04:
        return ""
    if region in REGION_VARIANTS and random.random() < 0.35:
        return random.choice(REGION_VARIANTS[region])
    return region


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def random_date(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))


def generate_customers(n_customers: int = 1000) -> list[dict]:
    rows: list[dict] = []
    used_emails: list[str] = []
    city_names = list(CITY_REGION)

    for customer_id in range(1, n_customers + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        full_name = f"{first} {last}"
        base_email = f"{first.lower()}.{last.lower().replace(' ', '')}{customer_id}@mexora.ma"
        email = base_email
        if used_emails and random.random() < 0.045:
            email = random.choice(used_emails)
        if random.random() < 0.035:
            email = ""
        if random.random() < 0.02:
            email = email.replace("@", "")
        used_emails.append(base_email)

        city = random.choices(city_names, weights=[18, 8, 17, 14, 9, 8, 7, 6, 4, 4, 3, 2], k=1)[0]
        region = CITY_REGION[city]
        birth_year = random.randint(1960, 2006)
        birth_date = date(birth_year, random.randint(1, 12), random.randint(1, 28))
        registration = random_date(date(2024, 1, 1), date(2026, 5, 15))

        rows.append(
            {
                "customer_id": customer_id,
                "full_name": full_name,
                "email": email,
                "phone": "" if random.random() < 0.055 else f"06{random.randint(10000000, 99999999)}",
                "city": choose_dirty_city(city),
                "region": choose_dirty_region(region),
                "registration_date": mixed_date(registration),
                "gender": random.choice(["Male", "Female", "M", "F", "Homme", "Femme", ""]),
                "birth_date": mixed_date(birth_date),
            }
        )
    return rows


def generate_products(n_products: int = 300) -> list[dict]:
    rows: list[dict] = []
    product_specs = [
        (category, sub_category, price_range)
        for category, sub_categories in PRODUCT_CATALOG.items()
        for sub_category, price_range in sub_categories.items()
    ]

    for product_id in range(1, n_products + 1):
        category, sub_category, price_range = product_specs[(product_id - 1) % len(product_specs)]
        low, high = price_range
        price = round(random.uniform(low, high), 2)
        if random.random() < 0.025:
            price = -abs(price)
        if random.random() < 0.015:
            price = round(random.uniform(60000, 120000), 2)
        rows.append(
            {
                "product_id": product_id,
                "product_name": f"{random.choice(BRANDS[category])} {sub_category} {product_id:03d}",
                "category": category,
                "sub_category": sub_category,
                "brand": random.choice(BRANDS[category]),
                "supplier": random.choice(SUPPLIERS),
                "price": price,
                "created_at": mixed_date(random_date(date(2024, 1, 1), date(2026, 1, 31))),
            }
        )
    return rows


def generate_orders_and_children(customers: list[dict], products: list[dict], n_orders: int = 5000) -> dict[str, list[dict]]:
    orders: list[dict] = []
    items: list[dict] = []
    payments: list[dict] = []
    deliveries: list[dict] = []
    returns: list[dict] = []
    order_totals: dict[int, float] = defaultdict(float)
    item_id = 1
    payment_id = 1
    delivery_id = 1
    return_id = 1

    product_by_id = {int(p["product_id"]): p for p in products}
    city_names = list(CITY_REGION)
    order_items_index: list[dict] = []

    for order_id in range(1, n_orders + 1):
        customer = random.choice(customers)
        order_date = random_date(date(2025, 1, 1), date(2026, 5, 20))
        order_status = random.choices(
            ORDER_STATUSES,
            weights=[66, 7, 8, 5, 3, 2, 2, 1, 2, 2, 2],
            k=1,
        )[0]
        n_items = random.choices([1, 2, 3, 4], weights=[42, 34, 18, 6], k=1)[0]

        for _ in range(n_items):
            product = product_by_id[random.randint(1, len(product_by_id))]
            quantity = random.randint(1, 5)
            if random.random() < 0.018:
                quantity = 0
            unit_price = float(product["price"])
            if unit_price <= 0 or unit_price > 50000:
                unit_price = round(random.uniform(60, 2500), 2)
            unit_price = round(unit_price * random.uniform(0.94, 1.08), 2)
            if random.random() < 0.012:
                unit_price = -abs(unit_price)
            if random.random() < 0.008:
                unit_price = round(random.uniform(75000, 150000), 2)
            discount = round(random.choice([0, 0.03, 0.05, 0.1, 0.15, 0.2]), 2)
            item_total = quantity * unit_price * (1 - discount)
            order_totals[order_id] += max(item_total, 0)
            row = {
                "order_item_id": item_id,
                "order_id": order_id,
                "product_id": product["product_id"],
                "quantity": quantity,
                "unit_price": unit_price,
                "discount_rate": discount,
            }
            items.append(row)
            order_items_index.append(row)
            item_id += 1

        if order_status in {"cancelled", "cancel"}:
            order_totals[order_id] = 0.0

        orders.append(
            {
                "order_id": order_id,
                "customer_id": customer["customer_id"],
                "order_date": mixed_date(order_date),
                "order_status": order_status,
                "total_amount": round(order_totals[order_id], 2),
            }
        )

        payment_status = random.choices(PAYMENT_STATUSES, weights=[77, 6, 4, 3, 3, 2, 2, 3], k=1)[0]
        amount_paid = 0 if order_status in {"cancelled", "cancel"} else order_totals[order_id]
        if payment_status in {"failed", "pending", "", "unknown"}:
            amount_paid = random.choice([0, round(amount_paid * random.uniform(0.2, 0.7), 2)])
        payments.append(
            {
                "payment_id": payment_id,
                "order_id": order_id,
                "payment_method": random.choice(PAYMENT_METHODS),
                "payment_status": payment_status,
                "payment_date": mixed_date(order_date + timedelta(days=random.randint(0, 3))),
                "amount_paid": round(amount_paid, 2),
            }
        )
        payment_id += 1

        delivery_city = random.choices(city_names, weights=[18, 8, 17, 14, 9, 8, 7, 6, 4, 4, 3, 2], k=1)[0]
        delivery_region = CITY_REGION[delivery_city]
        shipped_date = order_date + timedelta(days=random.randint(0, 3))
        delivered_date = shipped_date + timedelta(days=random.randint(1, 8))
        if random.random() < 0.012:
            delivered_date = order_date - timedelta(days=random.randint(1, 4))
        delivery_status = random.choices(DELIVERY_STATUSES, weights=[68, 8, 7, 4, 4, 3, 3, 3], k=1)[0]
        if order_status in {"cancelled", "cancel"} and random.random() < 0.7:
            delivery_status = "failed"
            delivered_date = None
        deliveries.append(
            {
                "delivery_id": delivery_id,
                "order_id": order_id,
                "delivery_city": choose_dirty_city(delivery_city),
                "delivery_region": choose_dirty_region(delivery_region),
                "delivery_status": delivery_status,
                "shipping_company": random.choice(SHIPPING_COMPANIES),
                "shipped_date": mixed_date(shipped_date),
                "delivered_date": mixed_date(delivered_date),
            }
        )
        delivery_id += 1

    returnable_orders = random.sample(range(1, n_orders + 1), k=random.randint(int(n_orders * 0.05), int(n_orders * 0.15)))
    items_by_order: dict[int, list[dict]] = defaultdict(list)
    for row in order_items_index:
        items_by_order[int(row["order_id"])].append(row)

    for order_id in returnable_orders:
        if not items_by_order[order_id]:
            continue
        item = random.choice(items_by_order[order_id])
        refund_amount = max(float(item["unit_price"]) * int(item["quantity"]) * (1 - float(item["discount_rate"])), 0)
        returns.append(
            {
                "return_id": return_id,
                "order_id": order_id,
                "product_id": item["product_id"],
                "return_reason": random.choice(RETURN_REASONS),
                "return_date": mixed_date(random_date(date(2025, 1, 5), date(2026, 5, 25))),
                "refund_amount": round(refund_amount, 2),
            }
        )
        return_id += 1

    duplicate_orders = random.sample(orders, k=max(10, int(n_orders * 0.01)))
    orders.extend(dict(row) for row in duplicate_orders)

    return {
        "orders": orders,
        "order_items": items,
        "payments": payments,
        "deliveries": deliveries,
        "returns": returns,
    }


MYSQL_DATE_COLUMNS = {
    "customers": {"registration_date", "birth_date"},
    "products": {"created_at"},
    "orders": {"order_date"},
    "payments": {"payment_date"},
    "deliveries": {"shipped_date", "delivered_date"},
    "returns": {"return_date"},
}


def rows_for_mysql(table_name: str, rows: list[dict]) -> list[dict]:
    date_columns = MYSQL_DATE_COLUMNS.get(table_name, set())
    prepared: list[dict] = []
    for row in rows:
        item = dict(row)
        for column in date_columns:
            item[column] = parse_date_for_mysql(item.get(column))
        for column, value in list(item.items()):
            if value == "":
                item[column] = None
        prepared.append(item)
    return prepared


def load_tables_to_mysql(tables: dict[str, list[dict]]) -> dict[str, int]:
    """Create mexora_oltp and load generated data into MySQL."""
    run_sql_file(OLTP_SCHEMA)
    engine = get_oltp_engine()
    loaded: dict[str, int] = {}
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for table_name in ["returns", "deliveries", "payments", "order_items", "orders", "products", "customers"]:
            conn.execute(text(f"TRUNCATE TABLE {quote_identifier(table_name)}"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

        for table_name, rows in tables.items():
            if not rows:
                loaded[table_name] = 0
                continue
            columns = list(rows[0].keys())
            column_sql = ", ".join(quote_identifier(column) for column in columns)
            value_sql = ", ".join(f":{column}" for column in columns)
            stmt = text(f"INSERT IGNORE INTO {quote_identifier(table_name)} ({column_sql}) VALUES ({value_sql})")
            prepared_rows = rows_for_mysql(table_name, rows)
            result = conn.execute(stmt, prepared_rows)
            loaded[table_name] = int(result.rowcount or 0)
    return loaded


def generate_tables() -> dict[str, list[dict]]:
    random.seed(RANDOM_SEED)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    customers = generate_customers()
    products = generate_products()
    child_tables = generate_orders_and_children(customers, products)

    tables = {
        "customers": customers,
        "products": products,
        **child_tables,
    }

    for table_name, rows in tables.items():
        write_csv(GENERATED_DIR / f"{table_name}.csv", rows)

    return tables


def main(load_mysql: bool = False) -> dict[str, Any]:
    tables = generate_tables()

    summary = {table_name: len(rows) for table_name, rows in tables.items()}
    print("Données générées dans", GENERATED_DIR)
    for table_name, row_count in summary.items():
        print(f"- {table_name}: {row_count}")
    payload: dict[str, Any] = {"generated_rows": summary}
    if load_mysql:
        try:
            mysql_summary = load_tables_to_mysql(tables)
        except SQLAlchemyError as exc:
            raise SystemExit(
                "Chargement MySQL OLTP impossible. Vérifiez que MySQL est démarré, "
                "copiez .env.example vers .env et renseignez MYSQL_PASSWORD / MEXORA_SOURCE_URL.\n"
                f"Détail: {exc}"
            ) from exc
        payload["mysql_loaded_rows"] = mysql_summary
        print("Données chargées dans MySQL mexora_oltp")
        for table_name, row_count in mysql_summary.items():
            print(f"- {table_name}: {row_count}")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Génération des données OLTP Mexora.")
    parser.add_argument("--load-mysql", action="store_true", help="Crée/remplit la base MySQL mexora_oltp.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(load_mysql=args.load_mysql)
