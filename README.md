# Mini-Projet 1 - Pipeline ETL & Data Warehouse pour Mexora

Projet BI/Data Warehouse pour Mexora, marketplace e-commerce fictive basée à Tanger.

## Description

Ce projet met en place une chaîne décisionnelle complète : une source transactionnelle MySQL, un pipeline ETL Python, un Data Warehouse MySQL en schéma en étoile, des requêtes analytiques MySQL et un dashboard BI Metabase.

Le rendu BI peut être exploré dans Metabase via le Data Warehouse MySQL `mexora_dw`. Streamlit reste disponible comme dashboard Python complémentaire.

Le cahier de charge recommande PostgreSQL pour le Data Warehouse. Le choix exécuté ici est MySQL isolé, car le système transactionnel imposé est MySQL et l'environnement local validé fonctionne sur `127.0.0.1:3307`. Pour couvrir les attentes académiques strictes, le dépôt contient aussi des scripts PostgreSQL de référence dans `sql/postgres/`, un package `mexora_etl/` structuré selon l'énoncé, les quatre fichiers bruts académiques demandés et les livrables de justification.

## Contexte Mexora

Mexora vend des produits au Maroc dans trois catégories :

- électronique ;
- mode ;
- alimentation.

Le Directeur Général souhaite suivre rapidement le chiffre d'affaires, les meilleurs clients, les performances par catégorie, les ventes par région, les retours et les délais de livraison.

## Architecture

```text
MySQL OLTP réel isolé sur 127.0.0.1:3307
        -> Extraction Python
        -> Zone raw CSV
        -> Transformation Pandas
        -> Data Warehouse MySQL mexora_dw
        -> Requêtes analytiques MySQL
        -> Metabase BI Dashboard
        -> Rapport PDF + GitHub
```

## Technologies

- Python
- Pandas
- MySQL
- SQLAlchemy
- PyMySQL
- python-dotenv
- Plotly
- Streamlit
- Java
- Metabase
- SQL
- Pandoc pour le PDF, si disponible

## Structure projet

```text
mexora-bi-project/
├── data/
│   ├── raw/
│   ├── processed/
│   ├── generated/
│   └── academic_raw/
├── sql/
│   ├── 01_oltp_schema.sql
│   ├── 02_insert_sample_data.sql
│   ├── 03_dw_schema.sql
│   ├── 04_analytics_queries.sql
│   ├── 05_quality_checks.sql
│   ├── 06_reporting_views_mysql.sql
│   ├── create_dwh.sql
│   ├── check_integrity.sql
│   └── postgres/
├── scripts/
│   ├── db_utils.py
│   ├── start_project_mysql.py
│   ├── generate_data.py
│   ├── generate_academic_assets.py
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   └── run_etl.py
├── mexora_etl/
│   ├── config/
│   ├── extract/
│   ├── transform/
│   ├── load/
│   ├── utils/
│   └── main.py
├── dashboard/
│   ├── streamlit_app.py
│   ├── dashboard_description.md
│   └── powerbi/
├── metabase/
│   ├── start_metabase.sh
│   ├── README_metabase.md
│   ├── create_mexora_dashboard.py
│   ├── questions_sql.md
│   └── dashboard_plan.md
├── docs/
│   ├── architecture.md
│   ├── assumptions.md
│   ├── data_dictionary.md
│   ├── er_schema_mexora.mmd
│   ├── modeling_justification.md
│   ├── modeling_justification.pdf
│   ├── rapport_transformations.md
│   ├── insights_metier.md
│   ├── insights_metier.pdf
│   └── quality_results.md
├── report/
│   ├── assets/
│   ├── rapport_mexora.md
│   └── rapport_mexora.pdf
├── .env.example
├── README.md
├── requirements.txt
└── .gitignore
```

## Installation

```bash
cd "/home/soufiane/DATAEng/Miniprojet 1/mexora-bi-project"
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Configuration

Copier le fichier d'exemple :

```bash
cp .env.example .env
```

Configuration validée :

```text
MYSQL_USER=mexora_user
MYSQL_PASSWORD=mexora_pass
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307

MEXORA_OLTP_DB=mexora_oltp
MEXORA_DW_DB=mexora_dw

MEXORA_SOURCE_URL=mysql+pymysql://mexora_user:mexora_pass@127.0.0.1:3307/mexora_oltp
MEXORA_DW_URL=mysql+pymysql://mexora_user:mexora_pass@127.0.0.1:3307/mexora_dw

MEXORA_AUTO_START_MYSQL=1
MEXORA_PROJECT_MYSQL_DIR=/tmp/mexora_mysql_project
MEXORA_PROJECT_MYSQL_ROOT_PASSWORD=root123
```

Ces identifiants sont des valeurs de démonstration locales. Le fichier `.env` ne doit pas être versionné.

## Lancement MySQL isolé

Le projet utilise une instance MySQL réelle isolée dans `/tmp/mexora_mysql_project`, sur le port `3307`.

```bash
python scripts/start_project_mysql.py
```

Le helper considère MySQL prêt uniquement si `mexora_user` peut se connecter en TCP à `127.0.0.1:3307` et ouvrir `mexora_oltp` et `mexora_dw`.

Vérification :

```bash
mysql -h 127.0.0.1 -P 3307 -u mexora_user -pmexora_pass mexora_oltp -e "SELECT DATABASE();"
mysql -h 127.0.0.1 -P 3307 -u mexora_user -pmexora_pass mexora_dw -e "SELECT DATABASE();"
```

## Lancement ETL

```bash
python scripts/run_etl.py --regenerate
```

Le pipeline :

1. génère les données réalistes et imparfaites ;
2. charge MySQL `mexora_oltp` ;
3. extrait les tables vers `data/raw/` ;
4. transforme et nettoie avec Pandas ;
5. construit les dimensions et `fact_sales` ;
6. charge MySQL `mexora_dw`.

## Livrables académiques du cahier de charge

Les fichiers bruts demandés par l'énoncé sont générés dans `data/academic_raw/` :

| Fichier | Rôle |
|---|---|
| `commandes_mexora.csv` | 50 000 lignes de commandes volontairement imparfaites |
| `produits_mexora.json` | catalogue produits avec catégories hétérogènes, prix manquants et produits inactifs |
| `clients_mexora.csv` | clients avec doublons, emails invalides et codifications hétérogènes |
| `regions_maroc.csv` | référentiel géographique propre |

Pour régénérer ces livrables, ainsi que le schéma étoile et les petits PDFs annexes :

```bash
python scripts/generate_academic_assets.py
```

Le package `mexora_etl/` reprend la structure imposée dans le cahier de charge :

```text
mexora_etl/
├── config/settings.py
├── extract/extractor.py
├── transform/clean_commandes.py
├── transform/clean_clients.py
├── transform/clean_produits.py
├── transform/build_dimensions.py
├── load/loader.py
├── utils/logger.py
└── main.py
```

L'exécution opérationnelle recommandée reste `scripts/run_etl.py`, car elle a été validée de bout en bout avec MySQL OLTP et MySQL DW.

## Lancement dashboard Metabase

Metabase est le dashboard BI final officiel du projet. Il est lancé depuis un dossier sans espace pour éviter l'erreur Java liée au chemin `Miniprojet 1`.

```bash
bash metabase/start_metabase.sh
```

Ouvrir ensuite :

```text
http://localhost:3000
```

Connexion Metabase à MySQL :

| Champ | Valeur |
|---|---|
| Type | MySQL |
| Host | `127.0.0.1` |
| Port | `3307` |
| Database | `mexora_dw` |
| Username | `mexora_user` |
| Password | `mexora_pass` |

### Automatisation du dashboard Metabase

Le dashboard `Mexora BI Dashboard` peut être généré via l'API Metabase, sans créer manuellement chaque question.

Créer le fichier local d'identifiants Metabase :

```bash
cp metabase/.metabase_env.example metabase/.metabase_env
```

Renseigner l'email et le mot de passe du compte administrateur Metabase dans `metabase/.metabase_env`, puis lancer :

```bash
python metabase/create_mexora_dashboard.py
```

Le script crée ou met à jour la collection `Mexora BI Project`, les questions SQL et le dashboard final. Les requêtes SQL sont disponibles dans `metabase/questions_sql.md`.

Si l'API Metabase retourne `Connections could not be acquired from the underlying database`, redémarrer Metabase puis relancer le script :

```bash
bash metabase/start_metabase.sh
python metabase/create_mexora_dashboard.py
```

Si Metabase retourne une erreur interne `REPORT_DASHBOARDCARD` ou `PRIMARY KEY`, les questions ont généralement été créées mais leur placement automatique dans le dashboard a échoué à cause du stockage interne Metabase. Dans ce cas, utiliser la méthode manuelle ci-dessous pour ajouter les cartes déjà créées au dashboard.

Méthode manuelle de secours :

1. ouvrir `http://localhost:3000` ;
2. créer `New > SQL Query` ;
3. coller les requêtes de `metabase/questions_sql.md` ;
4. sauvegarder les cartes dans la collection `Mexora BI Project` ;
5. utiliser `Add to dashboard > Mexora BI Dashboard` ;
6. répéter au minimum pour les cinq questions obligatoires du cahier.

## Dashboard Streamlit optionnel

Streamlit reste disponible comme prototype complémentaire :

```bash
streamlit run dashboard/streamlit_app.py
```

## Reporting matérialisé MySQL

Le cahier de charge recommande des vues matérialisées PostgreSQL. MySQL ne fournit pas de `MATERIALIZED VIEW` native ; le projet crée donc des tables de reporting rafraîchissables et indexées :

- `reporting_mv_ca_mensuel`
- `reporting_mv_top_produits`
- `reporting_mv_performance_livreurs`
- `dim_livreur`

```bash
mysql -h 127.0.0.1 -P 3307 -u mexora_user -pmexora_pass mexora_dw < sql/06_reporting_views_mysql.sql
```

Des scripts PostgreSQL de référence sont aussi disponibles pour une lecture strictement alignée avec l'énoncé :

```text
sql/postgres/01_create_dwh.sql
sql/postgres/02_check_integrity.sql
sql/postgres/03_reporting_materialized_views.sql
```

Les alias de livrables attendus sont :

```text
sql/create_dwh.sql
sql/check_integrity.sql
```

## Requêtes analytiques

```bash
mysql -h 127.0.0.1 -P 3307 -u mexora_user -pmexora_pass mexora_dw < sql/04_analytics_queries.sql
```

Le fichier contient les requêtes analytiques principales, plus les cinq questions obligatoires du cahier de charge : évolution CA région, top produits trimestriels Tanger, panier moyen par segment, taux de retour avec seuil d'alerte et effet Ramadan alimentation.

## Quality checks

```bash
mysql -h 127.0.0.1 -P 3307 -u mexora_user -pmexora_pass mexora_dw < sql/05_quality_checks.sql
```

Voir aussi `docs/quality_results.md`.

## Résultats validés

Dernière validation : 30 mai 2026.

| Indicateur | Valeur |
|---|---:|
| customers | 1000 |
| products | 300 |
| orders | 5000 |
| order_items | 9424 |
| payments | 5000 |
| deliveries | 5000 |
| returns | 738 |
| fact_sales | 9061 |
| anomalies détectées | 1559 |
| anomalies corrigées | 1196 |
| anomalies supprimées | 363 |
| taux de retour global | 7.87 % |
| délai moyen livraison | 14.99 jours |
| montants négatifs dans `fact_sales` | 0 |
| quantités invalides dans `fact_sales` | 0 |
| faits sans dimension correspondante | 0 |


## Auteur

Étudiant : Soufiane ZAARI  
Module : Data Engeneer 
Année universitaire : 2025-2026
