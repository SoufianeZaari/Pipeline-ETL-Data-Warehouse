"""Clean raw Mexora OLTP extracts and build the star schema files."""

from __future__ import annotations

import csv
import json
import statistics
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REFERENCE_DATE = date(2026, 5, 26)
RAMADAN_START = date(2026, 2, 18)
RAMADAN_END = date(2026, 3, 19)

REGION_BY_CITY = {
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
    "Unknown": "Unknown",
}

MONTH_NAMES = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def canon(value: Any) -> str:
    return strip_accents(str(value or "").strip().lower()).replace("_", " ").replace("-", " ")


def to_int(value: Any, default: int | None = None) -> int | None:
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def to_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d", "%b %d %Y", "%d %b %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return None


def date_text(value: date | None) -> str:
    return value.isoformat() if value else ""


def standardize_city(value: Any) -> str:
    key = canon(value)
    city_map = {
        "tanger": "Tanger",
        "tangier": "Tanger",
        "tng": "Tanger",
        "tnja": "Tanger",
        "casa": "Casablanca",
        "cas": "Casablanca",
        "casablanca": "Casablanca",
        "rabat": "Rabat",
        "tetouan": "Tétouan",
        "fes": "Fès",
        "marrakech": "Marrakech",
        "agadir": "Agadir",
        "oujda": "Oujda",
        "al hoceima": "Al Hoceïma",
        "kenitra": "Kénitra",
        "meknes": "Meknès",
        "nador": "Nador",
    }
    return city_map.get(key, str(value).strip() if str(value or "").strip() else "Unknown")


def standardize_region(value: Any, city: str = "Unknown") -> str:
    key = canon(value)
    region_map = {
        "tta": "Tanger-Tétouan-Al Hoceïma",
        "tanger tetouan": "Tanger-Tétouan-Al Hoceïma",
        "tanger tetouan al hoceima": "Tanger-Tétouan-Al Hoceïma",
        "casablanca settat": "Casablanca-Settat",
        "casa settat": "Casablanca-Settat",
        "rabat sale kenitra": "Rabat-Salé-Kénitra",
        "rsk": "Rabat-Salé-Kénitra",
        "fes meknes": "Fès-Meknès",
        "souss massa": "Souss-Massa",
        "oriental": "Oriental",
        "marrakech safi": "Marrakech-Safi",
    }
    if key in region_map:
        return region_map[key]
    if not key or key == "unknown":
        return REGION_BY_CITY.get(city, "Unknown")
    return str(value).strip()


def normalize_order_status(value: Any) -> str:
    key = canon(value)
    mapping = {
        "done": "completed",
        "ok": "completed",
        "completed": "completed",
        "livre": "completed",
        "cancel": "cancelled",
        "cancelled": "cancelled",
        "annule": "cancelled",
        "pending": "pending",
        "return": "returned",
        "returned": "returned",
        "failed": "failed",
        "ko": "failed",
    }
    return mapping.get(key, "unknown")


def normalize_delivery_status(value: Any) -> str:
    key = canon(value)
    mapping = {
        "livre": "delivered",
        "delivered": "delivered",
        "in transit": "in_transit",
        "delayed": "delayed",
        "failed": "failed",
        "ko": "failed",
    }
    return mapping.get(key, "unknown")


def normalize_payment_status(value: Any) -> str:
    key = canon(value)
    mapping = {
        "paid": "paid",
        "done": "paid",
        "ok": "paid",
        "pending": "pending",
        "failed": "failed",
        "ko": "failed",
        "unknown": "unknown",
        "": "unknown",
    }
    return mapping.get(key, "unknown")


def normalize_payment_method(value: Any) -> str:
    key = canon(value)
    mapping = {
        "cash on delivery": "Cash on Delivery",
        "credit card": "Credit Card",
        "bank transfer": "Bank Transfer",
        "wallet": "Wallet",
    }
    return mapping.get(key, str(value).strip() if str(value or "").strip() else "Unknown")


def issue(issues: list[dict[str, Any]], table: str, record_id: Any, issue_type: str, action: str, details: str) -> None:
    issues.append(
        {
            "table_name": table,
            "record_id": record_id,
            "issue_type": issue_type,
            "action": action,
            "details": details,
        }
    )


def remove_exact_duplicates(rows: list[dict[str, Any]], table: str, issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple] = set()
    deduped: list[dict[str, Any]] = []
    for row in rows:
        key = tuple((column, row.get(column)) for column in sorted(row))
        if key in seen:
            issue(issues, table, row.get(f"{table[:-1]}_id", ""), "exact_duplicate", "removed", "Ligne dupliquée exactement.")
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def age_group(birth_date: date | None) -> str:
    if not birth_date:
        return "Unknown"
    age = REFERENCE_DATE.year - birth_date.year - ((REFERENCE_DATE.month, REFERENCE_DATE.day) < (birth_date.month, birth_date.day))
    if age < 18:
        return "Under 18"
    if age <= 24:
        return "18-24"
    if age <= 34:
        return "25-34"
    if age <= 44:
        return "35-44"
    if age <= 54:
        return "45-54"
    return "55+"


def clean_customers(rows: list[dict[str, str]], issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = remove_exact_duplicates(rows, "customers", issues)
    cleaned: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    seen_emails: set[str] = set()

    for row in rows:
        customer_id = to_int(row.get("customer_id"))
        if customer_id is None or customer_id in seen_ids:
            issue(issues, "customers", row.get("customer_id"), "invalid_or_duplicate_customer_id", "removed", "Identifiant client invalide ou répété.")
            continue
        seen_ids.add(customer_id)

        email = str(row.get("email") or "").strip().lower()
        if "@" not in email or "." not in email.split("@")[-1]:
            email = f"unknown_email_{customer_id}@mexora.local"
            issue(issues, "customers", customer_id, "missing_or_invalid_email", "corrected", "Email remplacé par une valeur technique.")
        if email in seen_emails:
            email = f"duplicate_email_{customer_id}@mexora.local"
            issue(issues, "customers", customer_id, "duplicate_email", "corrected", "Email dupliqué remplacé par une valeur unique.")
        seen_emails.add(email)

        city = standardize_city(row.get("city"))
        if city == "Unknown":
            issue(issues, "customers", customer_id, "missing_city", "corrected", "Ville remplacée par Unknown.")
        region = standardize_region(row.get("region"), city)
        if region == "Unknown":
            issue(issues, "customers", customer_id, "missing_region", "corrected", "Région remplacée par Unknown.")

        registration_date = parse_date(row.get("registration_date"))
        if not registration_date:
            registration_date = date(2025, 1, 1)
            issue(issues, "customers", customer_id, "invalid_registration_date", "corrected", "Date d'inscription remplacée par 2025-01-01.")

        birth = parse_date(row.get("birth_date"))
        gender_key = canon(row.get("gender"))
        gender = {"m": "Male", "male": "Male", "homme": "Male", "f": "Female", "female": "Female", "femme": "Female"}.get(gender_key, "Unknown")

        cleaned.append(
            {
                "customer_id": customer_id,
                "full_name": str(row.get("full_name") or "Unknown").strip() or "Unknown",
                "email": email,
                "phone": str(row.get("phone") or "").strip() or "Unknown",
                "city": city,
                "region": region,
                "registration_date": date_text(registration_date),
                "gender": gender,
                "birth_date": date_text(birth),
                "age_group": age_group(birth),
            }
        )
    return cleaned


def clean_products(rows: list[dict[str, str]], issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = remove_exact_duplicates(rows, "products", issues)
    valid_prices_by_category: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        price = to_float(row.get("price"))
        if price and 0 < price <= 50000:
            valid_prices_by_category[str(row.get("category") or "Unknown")].append(price)

    default_price_by_category = {
        category: round(statistics.median(values), 2)
        for category, values in valid_prices_by_category.items()
        if values
    }

    cleaned: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    for row in rows:
        product_id = to_int(row.get("product_id"))
        if product_id is None or product_id in seen_ids:
            issue(issues, "products", row.get("product_id"), "invalid_or_duplicate_product_id", "removed", "Identifiant produit invalide ou répété.")
            continue
        seen_ids.add(product_id)
        category = str(row.get("category") or "Unknown").strip() or "Unknown"
        price = to_float(row.get("price"))
        if price is None or price <= 0 or price > 50000:
            price = default_price_by_category.get(category, 100.0)
            issue(issues, "products", product_id, "invalid_catalog_price", "corrected", "Prix catalogue négatif ou aberrant corrigé par la médiane de catégorie.")
        created_at = parse_date(row.get("created_at")) or date(2025, 1, 1)
        cleaned.append(
            {
                "product_id": product_id,
                "product_name": str(row.get("product_name") or f"Product {product_id}").strip(),
                "category": category,
                "sub_category": str(row.get("sub_category") or "Unknown").strip() or "Unknown",
                "brand": str(row.get("brand") or "Unknown").strip() or "Unknown",
                "supplier": str(row.get("supplier") or "Unknown").strip() or "Unknown",
                "price": round(price, 2),
                "created_at": date_text(created_at),
            }
        )
    return cleaned


def clean_orders(rows: list[dict[str, str]], valid_customer_ids: set[int], issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = remove_exact_duplicates(rows, "orders", issues)
    cleaned: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    for row in rows:
        order_id = to_int(row.get("order_id"))
        customer_id = to_int(row.get("customer_id"))
        if order_id is None or order_id in seen_ids:
            issue(issues, "orders", row.get("order_id"), "duplicate_order", "removed", "Commande dupliquée supprimée.")
            continue
        if customer_id not in valid_customer_ids:
            issue(issues, "orders", order_id, "unknown_customer", "removed", "Commande sans client valide.")
            continue
        order_date = parse_date(row.get("order_date"))
        if not order_date:
            issue(issues, "orders", order_id, "invalid_order_date", "removed", "Date de commande impossible.")
            continue
        seen_ids.add(order_id)
        status = normalize_order_status(row.get("order_status"))
        if status == "unknown":
            issue(issues, "orders", order_id, "unknown_order_status", "corrected", "Statut commande remplacé par unknown.")
        cleaned.append(
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "order_date": date_text(order_date),
                "order_status": status,
                "source_total_amount": round(to_float(row.get("total_amount"), 0.0) or 0.0, 2),
            }
        )
    return cleaned


def clean_order_items(
    rows: list[dict[str, str]],
    valid_order_ids: set[int],
    valid_product_ids: set[int],
    issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = remove_exact_duplicates(rows, "order_items", issues)
    cleaned: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    for row in rows:
        order_item_id = to_int(row.get("order_item_id"))
        order_id = to_int(row.get("order_id"))
        product_id = to_int(row.get("product_id"))
        if order_item_id is None or order_item_id in seen_ids:
            issue(issues, "order_items", row.get("order_item_id"), "duplicate_order_item", "removed", "Ligne de commande dupliquée.")
            continue
        if order_id not in valid_order_ids or product_id not in valid_product_ids:
            issue(issues, "order_items", order_item_id, "orphan_order_item", "removed", "Ligne sans commande ou produit valide.")
            continue
        quantity = to_int(row.get("quantity"), 0) or 0
        if quantity <= 0:
            issue(issues, "order_items", order_item_id, "invalid_quantity", "removed", "Quantité <= 0.")
            continue
        unit_price = to_float(row.get("unit_price"))
        if unit_price is None or unit_price <= 0 or unit_price > 50000:
            issue(issues, "order_items", order_item_id, "invalid_unit_price", "removed", "Prix unitaire négatif ou aberrant isolé.")
            continue
        discount_rate = to_float(row.get("discount_rate"), 0.0) or 0.0
        if discount_rate < 0 or discount_rate > 0.8:
            issue(issues, "order_items", order_item_id, "invalid_discount", "corrected", "Remise remplacée par 0.")
            discount_rate = 0.0
        seen_ids.add(order_item_id)
        cleaned.append(
            {
                "order_item_id": order_item_id,
                "order_id": order_id,
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": round(unit_price, 2),
                "discount_rate": round(discount_rate, 4),
            }
        )
    return cleaned


def clean_payments(rows: list[dict[str, str]], valid_order_ids: set[int], issues: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    rows = remove_exact_duplicates(rows, "payments", issues)
    cleaned: dict[int, dict[str, Any]] = {}
    for row in rows:
        payment_id = to_int(row.get("payment_id"))
        order_id = to_int(row.get("order_id"))
        if order_id not in valid_order_ids:
            issue(issues, "payments", payment_id, "orphan_payment", "removed", "Paiement sans commande valide.")
            continue
        if order_id in cleaned:
            issue(issues, "payments", payment_id, "duplicate_payment_order", "removed", "Paiement supplémentaire ignoré pour la même commande.")
            continue
        status = normalize_payment_status(row.get("payment_status"))
        if status == "unknown":
            issue(issues, "payments", payment_id, "unclear_payment_status", "corrected", "Statut paiement remplacé par unknown.")
        amount_paid = to_float(row.get("amount_paid"), 0.0) or 0.0
        if amount_paid < 0:
            amount_paid = 0.0
            issue(issues, "payments", payment_id, "negative_payment", "corrected", "Montant payé négatif remplacé par 0.")
        payment_date = parse_date(row.get("payment_date"))
        cleaned[order_id] = {
            "payment_id": payment_id,
            "order_id": order_id,
            "payment_method": normalize_payment_method(row.get("payment_method")),
            "payment_status": status,
            "payment_date": date_text(payment_date),
            "amount_paid": round(amount_paid, 2),
        }
    return cleaned


def clean_deliveries(
    rows: list[dict[str, str]],
    order_by_id: dict[int, dict[str, Any]],
    issues: list[dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    rows = remove_exact_duplicates(rows, "deliveries", issues)
    cleaned: dict[int, dict[str, Any]] = {}
    for row in rows:
        delivery_id = to_int(row.get("delivery_id"))
        order_id = to_int(row.get("order_id"))
        if order_id not in order_by_id:
            issue(issues, "deliveries", delivery_id, "orphan_delivery", "removed", "Livraison sans commande valide.")
            continue
        if order_id in cleaned:
            issue(issues, "deliveries", delivery_id, "duplicate_delivery_order", "removed", "Livraison supplémentaire ignorée pour la même commande.")
            continue

        order_date = parse_date(order_by_id[order_id]["order_date"])
        shipped_date = parse_date(row.get("shipped_date"))
        delivered_date = parse_date(row.get("delivered_date"))
        delivery_status = normalize_delivery_status(row.get("delivery_status"))
        if not shipped_date and order_date:
            shipped_date = order_date + timedelta(days=1)
            issue(issues, "deliveries", delivery_id, "missing_shipped_date", "corrected", "Date d'expédition estimée.")
        if shipped_date and order_date and shipped_date < order_date:
            shipped_date = order_date + timedelta(days=1)
            issue(issues, "deliveries", delivery_id, "shipped_before_order", "corrected", "Date d'expédition corrigée.")
        if delivery_status == "delivered" and not delivered_date and shipped_date:
            delivered_date = shipped_date + timedelta(days=3)
            issue(issues, "deliveries", delivery_id, "missing_delivered_date", "corrected", "Date de livraison estimée.")
        if delivered_date and order_date and delivered_date < order_date:
            delivered_date = (shipped_date or order_date) + timedelta(days=3)
            issue(issues, "deliveries", delivery_id, "delivered_before_order", "corrected", "Date de livraison corrigée.")

        delivery_city = standardize_city(row.get("delivery_city"))
        delivery_region = standardize_region(row.get("delivery_region"), delivery_city)
        delay = (delivered_date - order_date).days if delivered_date and order_date else None
        cleaned[order_id] = {
            "delivery_id": delivery_id,
            "order_id": order_id,
            "delivery_city": delivery_city,
            "delivery_region": delivery_region,
            "delivery_status": delivery_status,
            "shipping_company": str(row.get("shipping_company") or "Unknown").strip() or "Unknown",
            "shipped_date": date_text(shipped_date),
            "delivered_date": date_text(delivered_date),
            "delivery_delay_days": delay,
        }
    return cleaned


def clean_returns(
    rows: list[dict[str, str]],
    valid_order_ids: set[int],
    valid_product_ids: set[int],
    issues: list[dict[str, Any]],
) -> dict[tuple[int, int], dict[str, Any]]:
    rows = remove_exact_duplicates(rows, "returns", issues)
    cleaned: dict[tuple[int, int], dict[str, Any]] = {}
    seen_ids: set[int] = set()
    for row in rows:
        return_id = to_int(row.get("return_id"))
        order_id = to_int(row.get("order_id"))
        product_id = to_int(row.get("product_id"))
        if return_id is None or return_id in seen_ids:
            issue(issues, "returns", row.get("return_id"), "duplicate_return", "removed", "Retour dupliqué.")
            continue
        if order_id not in valid_order_ids or product_id not in valid_product_ids:
            issue(issues, "returns", return_id, "orphan_return", "removed", "Retour sans commande ou produit valide.")
            continue
        refund_amount = to_float(row.get("refund_amount"), 0.0) or 0.0
        if refund_amount < 0:
            refund_amount = 0.0
            issue(issues, "returns", return_id, "negative_refund", "corrected", "Remboursement négatif remplacé par 0.")
        seen_ids.add(return_id)
        cleaned[(order_id, product_id)] = {
            "return_id": return_id,
            "order_id": order_id,
            "product_id": product_id,
            "return_reason": str(row.get("return_reason") or "Unknown").strip() or "Unknown",
            "return_date": date_text(parse_date(row.get("return_date"))),
            "refund_amount": round(refund_amount, 2),
        }
    return cleaned


def build_dim_date(orders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order_dates = [parse_date(row["order_date"]) for row in orders if parse_date(row["order_date"])]
    start = min(order_dates) if order_dates else date(2025, 1, 1)
    end = max(order_dates) if order_dates else date(2026, 5, 25)
    rows: list[dict[str, Any]] = []
    current = start
    while current <= end:
        rows.append(
            {
                "date_key": int(current.strftime("%Y%m%d")),
                "full_date": current.isoformat(),
                "day": current.day,
                "month": current.month,
                "month_name": MONTH_NAMES[current.month],
                "quarter": (current.month - 1) // 3 + 1,
                "year": current.year,
                "is_weekend": 1 if current.weekday() >= 5 else 0,
                "is_ramadan": 1 if RAMADAN_START <= current <= RAMADAN_END else 0,
            }
        )
        current += timedelta(days=1)
    return rows


def segment_from_revenue(revenue: float) -> str:
    """Classify customers using the academic Gold/Silver/Bronze rule."""
    if revenue >= 15000:
        return "Gold"
    if revenue >= 5000:
        return "Silver"
    return "Bronze"


def transform(raw_dir: Path = RAW_DIR, processed_dir: Path = PROCESSED_DIR) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    processed_dir.mkdir(parents=True, exist_ok=True)

    raw_customers = read_csv(raw_dir / "customers.csv")
    raw_products = read_csv(raw_dir / "products.csv")
    raw_orders = read_csv(raw_dir / "orders.csv")
    raw_order_items = read_csv(raw_dir / "order_items.csv")
    raw_payments = read_csv(raw_dir / "payments.csv")
    raw_deliveries = read_csv(raw_dir / "deliveries.csv")
    raw_returns = read_csv(raw_dir / "returns.csv")

    customers = clean_customers(raw_customers, issues)
    products = clean_products(raw_products, issues)
    orders = clean_orders(raw_orders, {row["customer_id"] for row in customers}, issues)
    order_by_id = {row["order_id"]: row for row in orders}
    order_items = clean_order_items(raw_order_items, set(order_by_id), {row["product_id"] for row in products}, issues)
    payments = clean_payments(raw_payments, set(order_by_id), issues)
    deliveries = clean_deliveries(raw_deliveries, order_by_id, issues)
    returns = clean_returns(raw_returns, set(order_by_id), {row["product_id"] for row in products}, issues)

    dim_customer = []
    customer_key_by_id = {}
    for key, row in enumerate(sorted(customers, key=lambda item: item["customer_id"]), start=1):
        customer_key_by_id[row["customer_id"]] = key
        dim_customer.append(
            {
                "customer_key": key,
                "customer_id": row["customer_id"],
                "full_name": row["full_name"],
                "gender": row["gender"],
                "age_group": row["age_group"],
                "city": row["city"],
                "region": row["region"],
                "registration_date": row["registration_date"],
            }
        )

    dim_product = []
    product_key_by_id = {}
    for key, row in enumerate(sorted(products, key=lambda item: item["product_id"]), start=1):
        product_key_by_id[row["product_id"]] = key
        dim_product.append(
            {
                "product_key": key,
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "category": row["category"],
                "sub_category": row["sub_category"],
                "brand": row["brand"],
                "supplier": row["supplier"],
            }
        )

    dim_date = build_dim_date(orders)
    date_key_by_date = {row["full_date"]: row["date_key"] for row in dim_date}

    region_values = {(row["city"], row["region"]) for row in customers}
    region_values.update((row["delivery_city"], row["delivery_region"]) for row in deliveries.values())
    dim_region = []
    region_key_by_pair = {}
    for key, (city, region) in enumerate(sorted(region_values), start=1):
        region_key_by_pair[(city, region)] = key
        dim_region.append({"region_key": key, "city": city, "region": region, "country": "Maroc"})

    payment_values = {(row["payment_method"], row["payment_status"]) for row in payments.values()}
    payment_values.add(("Unknown", "unknown"))
    dim_payment = []
    payment_key_by_pair = {}
    for key, (method, status) in enumerate(sorted(payment_values), start=1):
        payment_key_by_pair[(method, status)] = key
        dim_payment.append({"payment_key": key, "payment_method": method, "payment_status": status})

    delivery_values = {
        (row["delivery_status"], row["shipping_company"], row["delivery_city"], row["delivery_region"])
        for row in deliveries.values()
    }
    delivery_values.add(("unknown", "Unknown", "Unknown", "Unknown"))
    dim_delivery = []
    delivery_key_by_tuple = {}
    for key, item in enumerate(sorted(delivery_values), start=1):
        delivery_key_by_tuple[item] = key
        dim_delivery.append(
            {
                "delivery_key": key,
                "delivery_status": item[0],
                "shipping_company": item[1],
                "delivery_city": item[2],
                "delivery_region": item[3],
            }
        )

    order_total_by_order: dict[int, float] = defaultdict(float)
    for item in order_items:
        order_total_by_order[item["order_id"]] += round(item["quantity"] * item["unit_price"] * (1 - item["discount_rate"]), 2)

    consumed_returns: set[tuple[int, int]] = set()
    fact_sales: list[dict[str, Any]] = []
    sales_key = 1
    for item in sorted(order_items, key=lambda row: row["order_item_id"]):
        order = order_by_id[item["order_id"]]
        payment = payments.get(item["order_id"], {"payment_method": "Unknown", "payment_status": "unknown", "amount_paid": 0.0})
        delivery = deliveries.get(
            item["order_id"],
            {
                "delivery_status": "unknown",
                "shipping_company": "Unknown",
                "delivery_city": "Unknown",
                "delivery_region": "Unknown",
                "delivery_delay_days": None,
            },
        )
        item_total = round(item["quantity"] * item["unit_price"] * (1 - item["discount_rate"]), 2)
        order_total = order_total_by_order[item["order_id"]]
        amount_paid = round((payment["amount_paid"] * item_total / order_total), 2) if order_total > 0 else 0.0
        return_key = (item["order_id"], item["product_id"])
        return_row = returns.get(return_key) if return_key not in consumed_returns else None
        if return_row:
            consumed_returns.add(return_key)
        region_pair = (delivery["delivery_city"], delivery["delivery_region"])
        delivery_tuple = (
            delivery["delivery_status"],
            delivery["shipping_company"],
            delivery["delivery_city"],
            delivery["delivery_region"],
        )
        fact_sales.append(
            {
                "sales_key": sales_key,
                "order_id": item["order_id"],
                "order_item_id": item["order_item_id"],
                "customer_key": customer_key_by_id[order["customer_id"]],
                "product_key": product_key_by_id[item["product_id"]],
                "date_key": date_key_by_date[order["order_date"]],
                "region_key": region_key_by_pair[region_pair],
                "payment_key": payment_key_by_pair[(payment["payment_method"], payment["payment_status"])],
                "delivery_key": delivery_key_by_tuple[delivery_tuple],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
                "discount_rate": item["discount_rate"],
                "total_amount": item_total,
                "amount_paid": amount_paid,
                "is_returned": 1 if return_row else 0,
                "refund_amount": return_row["refund_amount"] if return_row else 0.0,
                "delivery_delay_days": delivery["delivery_delay_days"] if delivery["delivery_delay_days"] is not None else "",
                "order_status": order["order_status"],
                "return_reason": return_row["return_reason"] if return_row else "",
            }
        )
        sales_key += 1

    revenue_by_customer_key: dict[int, float] = defaultdict(float)
    for row in fact_sales:
        if row["order_status"] in {"completed", "returned"}:
            revenue_by_customer_key[row["customer_key"]] += float(row["total_amount"])
    for row in dim_customer:
        row["segment_client"] = segment_from_revenue(revenue_by_customer_key.get(row["customer_key"], 0.0))

    write_csv(processed_dir / "dim_customer.csv", dim_customer)
    write_csv(processed_dir / "dim_product.csv", dim_product)
    write_csv(processed_dir / "dim_date.csv", dim_date)
    write_csv(processed_dir / "dim_region.csv", dim_region)
    write_csv(processed_dir / "dim_payment.csv", dim_payment)
    write_csv(processed_dir / "dim_delivery.csv", dim_delivery)
    write_csv(processed_dir / "fact_sales.csv", fact_sales)
    write_csv(
        processed_dir / "quality_issues.csv",
        issues,
        ["table_name", "record_id", "issue_type", "action", "details"],
    )

    actions = Counter(row["action"] for row in issues)
    summary = {
        "raw_rows": {
            "customers": len(raw_customers),
            "products": len(raw_products),
            "orders": len(raw_orders),
            "order_items": len(raw_order_items),
            "payments": len(raw_payments),
            "deliveries": len(raw_deliveries),
            "returns": len(raw_returns),
        },
        "processed_rows": {
            "dim_customer": len(dim_customer),
            "dim_product": len(dim_product),
            "dim_date": len(dim_date),
            "dim_region": len(dim_region),
            "dim_payment": len(dim_payment),
            "dim_delivery": len(dim_delivery),
            "fact_sales": len(fact_sales),
            "quality_issues": len(issues),
        },
        "quality_actions": dict(actions),
    }
    (processed_dir / "transform_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Transformation terminée.")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return summary


def main() -> dict[str, Any]:
    return transform()


if __name__ == "__main__":
    main()
