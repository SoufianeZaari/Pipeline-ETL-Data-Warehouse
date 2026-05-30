"""Automate creation of the Mexora BI dashboard in Metabase via REST API."""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".metabase_env"


@dataclass(frozen=True)
class Question:
    name: str
    sql: str
    display: str
    description: str


QUESTIONS: list[Question] = [
    Question("KPI - Chiffre d'affaires total", "SELECT ROUND(SUM(total_amount), 2) AS chiffre_affaires_total\nFROM fact_sales;", "scalar", "Chiffre d'affaires global."),
    Question("KPI - Nombre de commandes", "SELECT COUNT(DISTINCT order_id) AS nombre_commandes\nFROM fact_sales;", "scalar", "Nombre de commandes distinctes."),
    Question("KPI - Panier moyen", "SELECT ROUND(SUM(total_amount) / COUNT(DISTINCT order_id), 2) AS panier_moyen\nFROM fact_sales;", "scalar", "Panier moyen par commande."),
    Question("KPI - Taux de retour global", "SELECT ROUND(SUM(is_returned) * 100.0 / COUNT(*), 2) AS taux_retour_global\nFROM fact_sales;", "scalar", "Taux de retour global."),
    Question("KPI - Délai moyen livraison", "SELECT ROUND(AVG(delivery_delay_days), 2) AS delai_moyen_livraison\nFROM fact_sales;", "scalar", "Délai moyen de livraison."),
    Question("KPI - Montant remboursé total", "SELECT ROUND(SUM(refund_amount), 2) AS montant_rembourse_total\nFROM fact_sales;", "scalar", "Montant total remboursé."),
    Question("Chiffre d'affaires par mois", "SELECT \n    DATE_FORMAT(d.full_date, '%Y-%m') AS mois,\n    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires\nFROM fact_sales f\nJOIN dim_date d ON f.date_key = d.date_key\nGROUP BY DATE_FORMAT(d.full_date, '%Y-%m')\nORDER BY mois;", "line", "Évolution mensuelle du chiffre d'affaires."),
    Question("Chiffre d'affaires par région", "SELECT \n    r.region,\n    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires\nFROM fact_sales f\nJOIN dim_region r ON f.region_key = r.region_key\nGROUP BY r.region\nORDER BY chiffre_affaires DESC;", "bar", "Ventes par région."),
    Question("Chiffre d'affaires par catégorie", "SELECT \n    p.category,\n    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires\nFROM fact_sales f\nJOIN dim_product p ON f.product_key = p.product_key\nGROUP BY p.category\nORDER BY chiffre_affaires DESC;", "bar", "Ventes par catégorie produit."),
    Question("Chiffre d'affaires par ville", "SELECT \n    r.city,\n    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires\nFROM fact_sales f\nJOIN dim_region r ON f.region_key = r.region_key\nGROUP BY r.city\nORDER BY chiffre_affaires DESC;", "bar", "Ventes par ville."),
    Question("Top 10 clients", "SELECT \n    c.full_name,\n    c.city,\n    ROUND(SUM(f.total_amount), 2) AS total_depense\nFROM fact_sales f\nJOIN dim_customer c ON f.customer_key = c.customer_key\nGROUP BY c.full_name, c.city\nORDER BY total_depense DESC\nLIMIT 10;", "table", "Clients les plus contributeurs."),
    Question("Top 10 clients à Tanger", "SELECT \n    c.full_name,\n    ROUND(SUM(f.total_amount), 2) AS total_depense\nFROM fact_sales f\nJOIN dim_customer c ON f.customer_key = c.customer_key\nWHERE c.city = 'Tanger'\nGROUP BY c.full_name\nORDER BY total_depense DESC\nLIMIT 10;", "table", "Meilleurs clients à Tanger."),
    Question("Nombre de clients par région", "SELECT \n    region,\n    COUNT(DISTINCT customer_id) AS nombre_clients\nFROM dim_customer\nGROUP BY region\nORDER BY nombre_clients DESC;", "bar", "Répartition clients par région."),
    Question("Panier moyen par région", "SELECT \n    r.region,\n    ROUND(SUM(f.total_amount) / COUNT(DISTINCT f.order_id), 2) AS panier_moyen\nFROM fact_sales f\nJOIN dim_region r ON f.region_key = r.region_key\nGROUP BY r.region\nORDER BY panier_moyen DESC;", "bar", "Panier moyen régional."),
    Question("Top produits vendus", "SELECT \n    p.product_name,\n    p.category,\n    SUM(f.quantity) AS quantite_vendue,\n    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires\nFROM fact_sales f\nJOIN dim_product p ON f.product_key = p.product_key\nGROUP BY p.product_name, p.category\nORDER BY quantite_vendue DESC\nLIMIT 10;", "bar", "Produits les plus vendus."),
    Question("Produits les plus retournés", "SELECT \n    p.product_name,\n    p.category,\n    SUM(f.is_returned) AS total_retours\nFROM fact_sales f\nJOIN dim_product p ON f.product_key = p.product_key\nGROUP BY p.product_name, p.category\nORDER BY total_retours DESC\nLIMIT 10;", "bar", "Produits générant le plus de retours."),
    Question("Performance catégorie pendant Ramadan", "SELECT \n    p.category,\n    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires_ramadan\nFROM fact_sales f\nJOIN dim_product p ON f.product_key = p.product_key\nJOIN dim_date d ON f.date_key = d.date_key\nWHERE d.is_ramadan = 1\nGROUP BY p.category\nORDER BY chiffre_affaires_ramadan DESC;", "bar", "Performance des catégories pendant Ramadan."),
    Question("Quantité vendue par catégorie", "SELECT \n    p.category,\n    SUM(f.quantity) AS quantite_vendue\nFROM fact_sales f\nJOIN dim_product p ON f.product_key = p.product_key\nGROUP BY p.category\nORDER BY quantite_vendue DESC;", "bar", "Quantités vendues par catégorie."),
    Question("Taux de retour par région", "SELECT \n    r.region,\n    ROUND(SUM(f.is_returned) * 100.0 / COUNT(*), 2) AS taux_retour\nFROM fact_sales f\nJOIN dim_region r ON f.region_key = r.region_key\nGROUP BY r.region\nORDER BY taux_retour DESC;", "bar", "Taux de retour régional."),
    Question("Délai moyen livraison par région", "SELECT \n    r.region,\n    ROUND(AVG(f.delivery_delay_days), 2) AS delai_moyen_livraison\nFROM fact_sales f\nJOIN dim_region r ON f.region_key = r.region_key\nWHERE f.delivery_delay_days IS NOT NULL\nGROUP BY r.region\nORDER BY delai_moyen_livraison DESC;", "bar", "Délai moyen par région."),
    Question("Statuts de livraison", "SELECT \n    d.delivery_status,\n    COUNT(*) AS total\nFROM fact_sales f\nJOIN dim_delivery d ON f.delivery_key = d.delivery_key\nGROUP BY d.delivery_status\nORDER BY total DESC;", "pie", "Répartition des statuts de livraison."),
    Question("Répartition des paiements", "SELECT \n    p.payment_method,\n    COUNT(*) AS total\nFROM fact_sales f\nJOIN dim_payment p ON f.payment_key = p.payment_key\nGROUP BY p.payment_method\nORDER BY total DESC;", "pie", "Répartition des méthodes de paiement."),
    Question("Anomalies par type", "SELECT \n    issue_type,\n    COUNT(*) AS total\nFROM quality_issues\nGROUP BY issue_type\nORDER BY total DESC;", "bar", "Anomalies par type."),
    Question("Résumé qualité des données", "SELECT 'Anomalies détectées' AS indicateur, COUNT(*) AS valeur\nFROM quality_issues\nUNION ALL\nSELECT 'Montants négatifs dans fact_sales', COUNT(*)\nFROM fact_sales\nWHERE total_amount < 0\nUNION ALL\nSELECT 'Quantités invalides dans fact_sales', COUNT(*)\nFROM fact_sales\nWHERE quantity <= 0\nUNION ALL\nSELECT 'Faits sans customer', COUNT(*)\nFROM fact_sales f\nLEFT JOIN dim_customer c ON f.customer_key = c.customer_key\nWHERE c.customer_key IS NULL;", "table", "Contrôles qualité synthétiques."),
    Question("Cahier - Evolution CA mensuelle par région", "WITH bornes AS (\n    SELECT MAX(d.full_date) AS max_date\n    FROM fact_sales f\n    JOIN dim_date d ON f.date_key = d.date_key\n), ca_region_mois AS (\n    SELECT\n        DATE_FORMAT(d.full_date, '%Y-%m') AS mois,\n        r.region,\n        ROUND(SUM(f.total_amount), 2) AS chiffre_affaires\n    FROM fact_sales f\n    JOIN dim_date d ON f.date_key = d.date_key\n    JOIN dim_region r ON f.region_key = r.region_key\n    CROSS JOIN bornes b\n    WHERE f.order_status IN ('completed', 'returned')\n      AND d.full_date >= DATE_SUB(b.max_date, INTERVAL 12 MONTH)\n    GROUP BY DATE_FORMAT(d.full_date, '%Y-%m'), r.region\n)\nSELECT\n    mois,\n    region,\n    chiffre_affaires,\n    RANK() OVER (PARTITION BY mois ORDER BY chiffre_affaires DESC) AS rang_region_mois,\n    LAG(chiffre_affaires) OVER (PARTITION BY region ORDER BY mois) AS ca_mois_precedent,\n    ROUND(\n        (chiffre_affaires - LAG(chiffre_affaires) OVER (PARTITION BY region ORDER BY mois))\n        * 100.0 / NULLIF(LAG(chiffre_affaires) OVER (PARTITION BY region ORDER BY mois), 0),\n        2\n    ) AS evolution_pct\nFROM ca_region_mois\nORDER BY mois, rang_region_mois, chiffre_affaires DESC;", "line", "Question 1 du cahier de charge : évolution mensuelle du CA par région avec comparaison à la période précédente et rang de top région."),
    Question("Cahier - Top produits trimestriels à Tanger", "WITH ventes_tanger AS (\n    SELECT\n        d.year,\n        d.quarter,\n        p.product_name,\n        p.category,\n        SUM(f.quantity) AS quantite_vendue,\n        ROUND(SUM(f.total_amount), 2) AS chiffre_affaires\n    FROM fact_sales f\n    JOIN dim_date d ON f.date_key = d.date_key\n    JOIN dim_product p ON f.product_key = p.product_key\n    JOIN dim_region r ON f.region_key = r.region_key\n    WHERE r.city = 'Tanger'\n      AND f.order_status IN ('completed', 'returned')\n    GROUP BY d.year, d.quarter, p.product_name, p.category\n), ranked AS (\n    SELECT\n        ventes_tanger.*,\n        ROW_NUMBER() OVER (PARTITION BY year, quarter ORDER BY chiffre_affaires DESC, quantite_vendue DESC) AS rang_trimestre\n    FROM ventes_tanger\n)\nSELECT\n    year,\n    quarter,\n    rang_trimestre,\n    product_name,\n    category,\n    quantite_vendue,\n    chiffre_affaires\nFROM ranked\nWHERE rang_trimestre <= 10\nORDER BY year DESC, quarter DESC, rang_trimestre;", "bar", "Question 2 du cahier de charge : top 10 produits vendus par trimestre à Tanger avec ranking."),
    Question("Cahier - Panier moyen par segment client", "SELECT\n    c.segment_client,\n    COUNT(DISTINCT f.order_id) AS nb_commandes,\n    ROUND(SUM(f.total_amount) / NULLIF(COUNT(DISTINCT f.order_id), 0), 2) AS panier_moyen,\n    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires\nFROM fact_sales f\nJOIN dim_customer c ON f.customer_key = c.customer_key\nWHERE f.order_status IN ('completed', 'returned')\nGROUP BY c.segment_client\nORDER BY panier_moyen DESC;", "bar", "Question 3 du cahier de charge : panier moyen par segment client."),
    Question("Cahier - Taux retour catégorie avec alerte", "SELECT\n    p.category,\n    SUM(f.is_returned) AS nb_retours,\n    COUNT(*) AS nb_lignes,\n    ROUND(SUM(f.is_returned) * 100.0 / NULLIF(COUNT(*), 0), 2) AS taux_retour_pct,\n    CASE\n        WHEN SUM(f.is_returned) * 100.0 / NULLIF(COUNT(*), 0) > 5 THEN 'Rouge'\n        WHEN SUM(f.is_returned) * 100.0 / NULLIF(COUNT(*), 0) >= 3 THEN 'Orange'\n        ELSE 'Vert'\n    END AS niveau_alerte\nFROM fact_sales f\nJOIN dim_product p ON f.product_key = p.product_key\nGROUP BY p.category\nORDER BY taux_retour_pct DESC;", "table", "Question 4 du cahier de charge : taux de retour par catégorie avec seuil d'alerte."),
    Question("Cahier - Effet Ramadan alimentation", "WITH ventes_food_jour AS (\n    SELECT\n        d.full_date,\n        d.is_ramadan,\n        ROUND(SUM(f.total_amount), 2) AS ca_journalier,\n        SUM(f.quantity) AS volume_journalier\n    FROM fact_sales f\n    JOIN dim_product p ON f.product_key = p.product_key\n    JOIN dim_date d ON f.date_key = d.date_key\n    WHERE p.category = 'Food'\n      AND f.order_status IN ('completed', 'returned')\n    GROUP BY d.full_date, d.is_ramadan\n), synthese AS (\n    SELECT\n        CASE WHEN is_ramadan = 1 THEN 'Ramadan' ELSE 'Hors Ramadan' END AS periode,\n        ROUND(SUM(ca_journalier), 2) AS chiffre_affaires,\n        SUM(volume_journalier) AS volume_vendu,\n        ROUND(AVG(ca_journalier), 2) AS ca_moyen_journalier\n    FROM ventes_food_jour\n    GROUP BY is_ramadan\n), reference AS (\n    SELECT ca_moyen_journalier AS ca_moyen_hors_ramadan\n    FROM synthese\n    WHERE periode = 'Hors Ramadan'\n)\nSELECT\n    s.periode,\n    s.chiffre_affaires,\n    s.volume_vendu,\n    s.ca_moyen_journalier,\n    ROUND(s.ca_moyen_journalier * 100.0 / NULLIF(r.ca_moyen_hors_ramadan, 0), 2) AS indice_performance_ramadan\nFROM synthese s\nCROSS JOIN reference r\nORDER BY s.periode DESC;", "bar", "Question 5 du cahier de charge : effet Ramadan sur l'alimentation avec indice de performance base 100."),
]


class MetabaseAPIError(RuntimeError):
    def __init__(self, method: str, path: str, status: int | str, response: Any, suggestion: str = "") -> None:
        self.method = method
        self.path = path
        self.status = status
        self.response = response
        self.suggestion = suggestion
        super().__init__(self.__str__())

    def __str__(self) -> str:
        payload = json.dumps(self.response, indent=2, ensure_ascii=False) if not isinstance(self.response, str) else self.response
        if len(payload) > 2500:
            payload = payload[:2500] + "\n... [réponse Metabase tronquée, consulter les logs Metabase pour le détail complet]"
        message = f"Erreur API Metabase\nEndpoint: {self.method} {self.path}\nStatus: {self.status}\nRéponse:\n{payload}"
        if self.suggestion:
            message += f"\nCorrection proposée: {self.suggestion}"
        return message


class MetabaseClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.session_token: str | None = None

    def request(self, method: str, path: str, body: dict[str, Any] | None = None, expected: tuple[int, ...] = (200,)) -> Any:
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Content-Type": "application/json"}
        if self.session_token:
            headers["X-Metabase-Session"] = self.session_token
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = response.read().decode("utf-8")
                parsed = json.loads(raw) if raw else {}
                if response.status not in expected:
                    raise MetabaseAPIError(method, path, response.status, parsed)
                return parsed
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                parsed_error: Any = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                parsed_error = raw
            raise MetabaseAPIError(method, path, exc.code, parsed_error, suggestion_for(method, path, exc.code)) from exc
        except urllib.error.URLError as exc:
            raise MetabaseAPIError(
                method,
                path,
                "connection_error",
                str(exc),
                "Vérifiez que Metabase est lancé avec: bash metabase/start_metabase.sh",
            ) from exc
        except (TimeoutError, socket.timeout, OSError) as exc:
            raise MetabaseAPIError(
                method,
                path,
                "timeout",
                str(exc),
                "Metabase écoute peut-être sur le port 3000 mais ne répond pas. Relancez le service Metabase puis réessayez.",
            ) from exc

    def login(self, email: str, password: str) -> None:
        last_error: MetabaseAPIError | None = None
        payload: dict[str, Any] | None = None
        for attempt in range(1, 4):
            try:
                payload = self.request("POST", "/api/session", {"username": email, "password": password})
                break
            except MetabaseAPIError as exc:
                last_error = exc
                transient = exc.status in {"timeout", "connection_error"} or "Connections could not be acquired" in str(exc.response)
                if not transient or attempt == 3:
                    raise
                wait_seconds = attempt * 5
                print(f"Metabase n'est pas encore prêt pour l'API, nouvelle tentative dans {wait_seconds}s...", file=sys.stderr)
                time.sleep(wait_seconds)
        if payload is None:
            raise last_error or MetabaseAPIError("POST", "/api/session", "unknown", "Aucune réponse Metabase.")
        token = payload.get("id")
        if not token:
            raise MetabaseAPIError("POST", "/api/session", 200, payload, "La session ne contient pas de token id.")
        self.session_token = token


def suggestion_for(method: str, path: str, status: int) -> str:
    if path == "/api/session" and status in {400, 401, 403}:
        return (
            "Vérifiez METABASE_EMAIL et METABASE_PASSWORD dans metabase/.metabase_env. "
            "Si la réponse mentionne l'underlying database, redémarrez Metabase avec bash metabase/start_metabase.sh."
        )
    if status == 404 and "dash" in path:
        return "La version Metabase peut utiliser un endpoint différent pour ajouter une card au dashboard."
    if status in {401, 403}:
        return "L'utilisateur Metabase doit avoir les droits de créer des questions et dashboards."
    return "Consultez http://localhost:3000/api/docs puis adaptez l'endpoint si nécessaire."


def load_env() -> dict[str, str]:
    if not ENV_FILE.exists():
        raise SystemExit(
            "Configuration Metabase manquante.\n"
            "Créez metabase/.metabase_env à partir de metabase/.metabase_env.example puis relancez.\n"
            "Variables attendues: METABASE_URL, METABASE_EMAIL, METABASE_PASSWORD, METABASE_DATABASE_NAME."
        )
    values: dict[str, str] = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    for key, default in {
        "METABASE_URL": "http://localhost:3000",
        "METABASE_DATABASE_NAME": "Mexora Data Warehouse",
    }.items():
        values.setdefault(key, default)
    missing = [key for key in ("METABASE_EMAIL", "METABASE_PASSWORD") if not values.get(key)]
    if missing:
        raise SystemExit(f"Variables manquantes dans {ENV_FILE}: {', '.join(missing)}")
    return values


def as_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "models", "items"):
            if isinstance(payload.get(key), list):
                return payload[key]
    return []


def canonical_database_label(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[_-]+", " ", text)
    text = re.sub(r"\bdw\b", "data warehouse", text)
    text = re.sub(r"\s+", " ", text)
    return text


def get_database_id(client: MetabaseClient, database_name: str) -> int:
    payload = client.request("GET", "/api/database")
    databases = as_list(payload)
    requested = canonical_database_label(database_name)
    for database in databases:
        details = database.get("details") if isinstance(database.get("details"), dict) else {}
        candidates = {
            database.get("name"),
            database.get("id"),
            details.get("dbname"),
            details.get("db"),
            details.get("database"),
        }
        if any(canonical_database_label(candidate) == requested for candidate in candidates):
            return int(database["id"])

    # Friendly fallback for the project convention:
    # .env may use the physical MySQL database name mexora_dw while Metabase
    # displays it as "Mexora Data Warehouse".
    if requested == "mexora data warehouse":
        for database in databases:
            display_name = canonical_database_label(database.get("name"))
            if "mexora" in display_name and "data warehouse" in display_name:
                return int(database["id"])

    names = [database.get("name") for database in databases]
    raise SystemExit(
        f"Base Metabase introuvable: {database_name}. Bases disponibles: {names}\n"
        "Correction possible: utilisez METABASE_DATABASE_NAME=Mexora Data Warehouse "
        "ou le nom physique MySQL METABASE_DATABASE_NAME=mexora_dw."
    )



def find_collection(client: MetabaseClient, name: str) -> dict[str, Any] | None:
    payload = client.request("GET", "/api/collection")
    for collection in as_list(payload):
        if collection.get("name") == name:
            return collection
    return None


def ensure_collection(client: MetabaseClient, name: str) -> int:
    existing = find_collection(client, name)
    if existing:
        return int(existing["id"])
    created = client.request(
        "POST",
        "/api/collection",
        {"name": name, "description": "Questions et dashboard du mini-projet Mexora BI."},
        expected=(200, 201),
    )
    return int(created["id"])


def search_model(client: MetabaseClient, model: str, name: str) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode({"q": name, "models": model})
    try:
        payload = client.request("GET", f"/api/search?{query}")
        return [item for item in as_list(payload) if item.get("name") == name]
    except MetabaseAPIError:
        return []


def find_card(client: MetabaseClient, name: str, collection_id: int) -> dict[str, Any] | None:
    for item in search_model(client, "card", name):
        if item.get("collection_id") in {collection_id, str(collection_id)}:
            return item
    try:
        payload = client.request("GET", "/api/card")
        for card in as_list(payload):
            if card.get("name") == name and card.get("collection_id") in {collection_id, str(collection_id)}:
                return card
    except MetabaseAPIError:
        pass
    return None


def card_payload(question: Question, database_id: int, collection_id: int) -> dict[str, Any]:
    return {
        "name": question.name,
        "description": question.description,
        "dataset_query": {
            "type": "native",
            "database": database_id,
            "native": {"query": question.sql},
        },
        "display": question.display,
        "visualization_settings": {},
        "collection_id": collection_id,
    }


def ensure_card(client: MetabaseClient, question: Question, database_id: int, collection_id: int) -> tuple[int, str]:
    payload = card_payload(question, database_id, collection_id)
    existing = find_card(client, question.name, collection_id)
    if existing:
        card_id = int(existing["id"])
        client.request("PUT", f"/api/card/{card_id}", payload)
        return card_id, "updated"
    created = client.request("POST", "/api/card", payload, expected=(200, 201))
    return int(created["id"]), "created"


def find_dashboard(client: MetabaseClient, name: str, collection_id: int) -> dict[str, Any] | None:
    for item in search_model(client, "dashboard", name):
        if item.get("collection_id") in {collection_id, str(collection_id)}:
            return item
    try:
        payload = client.request("GET", "/api/dashboard")
        for dashboard in as_list(payload):
            if dashboard.get("name") == name and dashboard.get("collection_id") in {collection_id, str(collection_id)}:
                return dashboard
    except MetabaseAPIError:
        pass
    return None


def ensure_dashboard(client: MetabaseClient, name: str, collection_id: int) -> int:
    existing = find_dashboard(client, name, collection_id)
    if existing:
        return int(existing["id"])
    created = client.request(
        "POST",
        "/api/dashboard",
        {
            "name": name,
            "description": "Dashboard BI automatisé pour le Data Warehouse Mexora.",
            "collection_id": collection_id,
        },
        expected=(200, 201),
    )
    return int(created["id"])


def layout_for(index: int) -> dict[str, int]:
    if index < 6:
        return {"row": 0, "col": index * 4, "sizeX": 4, "sizeY": 3}
    offset = index - 6
    return {
        "row": 4 + (offset // 2) * 7,
        "col": 0 if offset % 2 == 0 else 12,
        "sizeX": 12,
        "sizeY": 7,
    }


def dashboard_card_ids(client: MetabaseClient, dashboard_id: int) -> set[int]:
    payload = client.request("GET", f"/api/dashboard/{dashboard_id}")
    ids: set[int] = set()
    for dashcard in payload.get("dashcards", []) or []:
        if dashcard.get("card_id"):
            ids.add(int(dashcard["card_id"]))
        elif isinstance(dashcard.get("card"), dict) and dashcard["card"].get("id"):
            ids.add(int(dashcard["card"]["id"]))
    return ids


def dashcard_payload(card_id: int, dashcard_id: int, layout: dict[str, int]) -> dict[str, Any]:
    return {
        "id": dashcard_id,
        "card_id": card_id,
        "row": layout["row"],
        "col": layout["col"],
        "size_x": layout["sizeX"],
        "size_y": layout["sizeY"],
        "parameter_mappings": [],
        "inline_parameters": [],
        "series": [],
    }


def sync_dashboard_cards(client: MetabaseClient, dashboard_id: int, card_ids: list[int]) -> int:
    dashboard = client.request("GET", f"/api/dashboard/{dashboard_id}")
    existing_by_card_id: dict[int, dict[str, Any]] = {}
    for dashcard in dashboard.get("dashcards", []) or []:
        card_id = dashcard.get("card_id")
        if not card_id and isinstance(dashcard.get("card"), dict):
            card_id = dashcard["card"].get("id")
        if card_id:
            existing_by_card_id[int(card_id)] = dashcard

    added = 0
    dashcards: list[dict[str, Any]] = []
    for index, card_id in enumerate(card_ids):
        existing = existing_by_card_id.get(card_id)
        if existing:
            dashcard_id = int(existing["id"])
        else:
            # Metabase v0.61 accepts temporary negative ids for new dashcards
            # when syncing the dashboard through PUT /api/dashboard/{id}.
            dashcard_id = -(index + 1)
            added += 1
        dashcards.append(dashcard_payload(card_id, dashcard_id, layout_for(index)))

    payload = {
        "name": dashboard.get("name") or "Mexora BI Dashboard",
        "description": dashboard.get("description") or "Dashboard BI automatisé pour le Data Warehouse Mexora.",
        "collection_id": dashboard.get("collection_id"),
        "parameters": dashboard.get("parameters") or [],
        "tabs": dashboard.get("tabs") or [],
        "dashcards": dashcards,
    }
    client.request("PUT", f"/api/dashboard/{dashboard_id}", payload)
    return added


def main() -> int:
    env = load_env()
    client = MetabaseClient(env["METABASE_URL"])
    client.login(env["METABASE_EMAIL"], env["METABASE_PASSWORD"])

    database_id = get_database_id(client, env["METABASE_DATABASE_NAME"])
    collection_id = ensure_collection(client, "Mexora BI Project")
    dashboard_id = ensure_dashboard(client, "Mexora BI Dashboard", collection_id)

    created = 0
    updated = 0
    card_ids: list[int] = []
    errors: list[str] = []
    warnings: list[str] = []

    for question in QUESTIONS:
        try:
            card_id, action = ensure_card(client, question, database_id, collection_id)
            card_ids.append(card_id)
            created += action == "created"
            updated += action == "updated"
        except Exception as exc:  # noqa: BLE001 - report every card error and continue
            errors.append(f"{question.name}: {exc}")

    existing_dashboard_cards = dashboard_card_ids(client, dashboard_id)
    dashboard_cards_added = 0
    try:
        dashboard_cards_added = sync_dashboard_cards(client, dashboard_id, card_ids)
    except Exception as exc:  # noqa: BLE001
        warnings.append(
            "Synchronisation dashboard: les questions ont été créées/mises à jour, "
            "mais Metabase a refusé le placement automatique des cartes. "
            "Ajoutez-les manuellement au dashboard si elles n'apparaissent pas. "
            f"Détail: {exc}"
        )

    dashboard_url = f"{env['METABASE_URL'].rstrip('/')}/dashboard/{dashboard_id}"
    print("Dashboard Metabase créé ou mis à jour.")
    print(f"URL du dashboard: {dashboard_url}")
    print(f"Questions créées: {created}")
    print(f"Questions mises à jour: {updated}")
    print(f"Cards déjà présentes dans le dashboard: {len(existing_dashboard_cards)}")
    print(f"Cards ajoutées au dashboard: {dashboard_cards_added}")
    print(f"Avertissements: {len(warnings)}")
    for warning in warnings:
        print(f"- {warning}")
    print(f"Erreurs: {len(errors)}")
    for error in errors:
        print(f"- {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MetabaseAPIError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc
