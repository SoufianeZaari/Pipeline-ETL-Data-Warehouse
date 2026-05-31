# Miniprojet 1 — Pipeline ETL & Data Warehouse Mexora

Projet BI/Data Warehouse complet pour **Mexora**, marketplace e-commerce fictive basée à Tanger.

## Description

Ce projet implémente une chaîne décisionnelle complète :

1. **4 fichiers bruts académiques** intentionnellement défectueux (`data/academic_raw/`)
2. **Pipeline ETL Python** (`mexora_etl/`) — extraction, transformation (14+ règles), chargement
3. **Data Warehouse PostgreSQL** en schéma en étoile (5 dimensions + table de faits)
4. **3 vues matérialisées** PostgreSQL dans le schéma `reporting_mexora`
5. **Metabase** comme dashboard BI local (conforme au cahier de charge)
6. **Streamlit** comme version web déployable sur Streamlit Cloud

> Le pipeline ETL académique (`mexora_etl/main.py`) cible PostgreSQL.
> Metabase reste le dashboard BI officiel du projet.
> Streamlit est ajouté comme interface web déployable, autonome via des exports CSV.

## Architecture

```text
data/academic_raw/        (50 000 commandes, 1 000 clients, 300 produits, régions)
        |
        v
mexora_etl/main.py        Extract -> Transform -> Load
        |
        v
PostgreSQL dwh_mexora     (3 schémas : staging / dwh / reporting)
        |
        +---> Metabase           (dashboard BI local, port 3000)
        +---> export_streamlit   (scripts/export_streamlit_data.py)
                |
                v
        dashboard/data/*.csv     (exports légers, versionnés GitHub)
                |
                v
        dashboard/streamlit_app.py  (déployable sur Streamlit Cloud)
```

## Structure projet

```text
mexora-bi-project/
├── data/
│   ├── academic_raw/        # fichiers bruts académiques (50k commandes, etc.)
│   ├── raw/                 # extractions MySQL OLTP
│   └── processed/
├── sql/
│   ├── postgres/
│   │   ├── 01_create_dwh.sql
│   │   ├── 02_check_integrity.sql
│   │   └── 03_reporting_materialized_views.sql
│   ├── create_dwh.sql
│   └── check_integrity.sql
├── mexora_etl/              # package ETL académique (structure CDC)
│   ├── config/settings.py
│   ├── extract/extractor.py
│   ├── transform/
│   │   ├── clean_commandes.py
│   │   ├── clean_clients.py
│   │   ├── clean_produits.py
│   │   └── build_dimensions.py
│   ├── load/loader.py
│   ├── utils/logger.py
│   └── main.py
├── scripts/
│   ├── run_etl.py
│   ├── export_streamlit_data.py   # <-- export CSV pour Streamlit
│   └── ...
├── dashboard/
│   ├── streamlit_app.py           # <-- dashboard Streamlit déployable
│   └── data/                      # CSV exportés depuis PostgreSQL
│       ├── kpis.csv
│       ├── ca_mensuel.csv
│       ├── ca_region.csv
│       ├── top_produits_tanger.csv
│       ├── segments_clients.csv
│       ├── taux_retour_categorie.csv
│       ├── ramadan_food.csv
│       └── livraison_retours.csv
├── metabase/                      # dashboard BI local (Metabase)
├── docs/
│   ├── er_schema_mexora.png       # L1 — schéma ER
│   ├── modeling_justification.pdf # L2 — justification choix
│   ├── rapport_transformations.md
│   └── insights_metier.pdf        # L8 — insights métier
├── report/
│   ├── rapport_mexora.tex         # rapport LaTeX source
│   └── rapport_mexora.pdf         # rapport PDF (18 pages)
├── .streamlit/config.toml
├── requirements.txt
└── .gitignore
```

## Installation

```bash
cd "Miniprojet 1/mexora-bi-project"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Lancer PostgreSQL local

```bash
# Démarrer l'instance locale (port 5433, socket /tmp/mexora_pg_socket)
/usr/lib/postgresql/16/bin/pg_ctl \
  -D /tmp/mexora_pg_data \
  -o "-p 5433 -k /tmp/mexora_pg_socket" \
  -l /tmp/mexora_pg.log start

# Vérifier
pg_isready -h /tmp/mexora_pg_socket -p 5433
```

## Lancer le pipeline ETL (PostgreSQL)

```bash
python -m mexora_etl.main
```

Résultat attendu :

```
[EXTRACT] Commandes : 50000 lignes
[TRANSFORM] Commandes : 50000 -> 46825 lignes
[BUILD] fait_ventes : 36203 lignes produites
[LOAD] dim_temps : 2557 lignes chargées
[LOAD] fait_ventes : 36203 lignes chargées
PIPELINE TERMINÉ EN 12 secondes
```

## Créer les vues matérialisées

```bash
psql -h /tmp/mexora_pg_socket -p 5433 -U $USER mexora_dwh \
  -f sql/postgres/03_reporting_materialized_views.sql
```

## Vérifier l'intégrité

```bash
psql -h /tmp/mexora_pg_socket -p 5433 -U $USER mexora_dwh \
  -f sql/postgres/02_check_integrity.sql
```

---

## Dashboard Streamlit déployable

> **Note :** Streamlit ne remplace pas Metabase. C'est une version web déployable
> qui consomme des exports CSV issus du Data Warehouse PostgreSQL.

### 1. Générer les données depuis PostgreSQL

```bash
python scripts/export_streamlit_data.py
```

Exporte 8 fichiers CSV dans `dashboard/data/` :
`kpis.csv`, `ca_mensuel.csv`, `ca_region.csv`, `top_produits_tanger.csv`,
`segments_clients.csv`, `taux_retour_categorie.csv`, `ramadan_food.csv`, `livraison_retours.csv`

### 2. Lancer localement

```bash
streamlit run dashboard/streamlit_app.py
```

Ouvre `http://localhost:8501` — 5 pages :
- 🏠 Vue générale (KPIs + CA mensuel + répartition catégories)
- 🗺️ Analyse régionale (CA par ville, évolution mensuelle)
- 👥 Clients & Segments (Gold/Silver/Bronze, panier moyen)
- 📦 Produits (top Tanger, CA catégorie)
- ↩️ Retours & Ramadan (alertes retours, effet Ramadan, livreurs)

### 3. Déployer sur Streamlit Cloud

1. Vérifier que `dashboard/data/*.csv` est commité dans le repo GitHub
2. Aller sur [share.streamlit.io](https://share.streamlit.io)
3. Se connecter avec le compte GitHub `SoufianeZaari`
4. Choisir le repo : `SoufianeZaari/Pipeline-ETL-Data-Warehouse`
5. Main file path : `dashboard/streamlit_app.py`
6. Cliquer **Deploy**

> L'app lit uniquement les CSV versionnés — aucune connexion PostgreSQL requise.

### 4. Important

- Le dashboard Streamlit **ne remplace pas le pipeline PostgreSQL** ; il consomme
  des exports issus du Data Warehouse.
- **Metabase reste le dashboard BI local** conforme au cahier de charge.
  Streamlit est la **version web déployable** de démonstration.
- Après chaque refresh ETL, régénérer les CSV avec `export_streamlit_data.py`
  et commit/push `dashboard/data/`.

---

## Dashboard Metabase (BI local officiel)

Metabase est le dashboard BI final officiel du projet (conforme au cahier de charge).

```bash
bash metabase/start_metabase.sh
```

Ouvrir : `http://localhost:3000`

Connexion Metabase vers PostgreSQL :

| Champ | Valeur |
|---|---|
| Type | PostgreSQL |
| Host | `/tmp/mexora_pg_socket` (ou `127.0.0.1`) |
| Port | `5433` |
| Database | `mexora_dwh` |
| Username | `$USER` |

---

## Livrables académiques

| # | Livrable | Fichier |
|---|---|---|
| L1 | Schéma ER annoté | `docs/er_schema_mexora.png` |
| L2 | Justification modélisation | `docs/modeling_justification.pdf` |
| L3 | Code Python ETL | `mexora_etl/` |
| L4 | Rapport transformations | `docs/rapport_transformations.md` |
| L5 | Script création DWH | `sql/postgres/01_create_dwh.sql` |
| L6 | Script intégrité | `sql/postgres/02_check_integrity.sql` |
| L7 | Dashboard | Metabase local + Streamlit Cloud |
| L8 | Insights métier | `docs/insights_metier.pdf` |
| — | Rapport complet | `report/rapport_mexora.pdf` |

## Résultats validés (pipeline PostgreSQL)

| Indicateur | Valeur |
|---|---:|
| Commandes extraites | 50 000 |
| Faits chargés | **36 203** |
| Clients | 898 |
| Produits | 300 |
| Entrées temporelles | 2 557 |
| Anomalies d'intégrité | **0** |
| Taux de retour global | 7,87 % |
| Délai moyen livraison | 14,99 jours |
| Vues matérialisées | 3 |

## Auteur

**Soufiane Zaari** — Module Data Engineering — 2025-2026
