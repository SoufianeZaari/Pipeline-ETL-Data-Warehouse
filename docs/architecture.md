# Architecture officielle

Le projet Mexora BI suit une architecture décisionnelle complète, construite autour d'un moteur MySQL réel et d'un dashboard Metabase.

```text
MySQL OLTP réel isolé sur 127.0.0.1:3307
        ↓
Extraction Python / SQLAlchemy
        ↓
Zone raw CSV
        ↓
Transformation Pandas et règles de qualité
        ↓
Data Warehouse MySQL mexora_dw
        ↓
Requêtes analytiques MySQL
        ↓
Dashboard Metabase BI
        ↓
Rapport PDF + repository GitHub
```

## Rôle de l'OLTP

La base MySQL `mexora_oltp` représente le système transactionnel de Mexora. Elle stocke les clients, produits, commandes, lignes de commande, paiements, livraisons et retours.

Ce modèle est adapté aux opérations quotidiennes : création de commandes, suivi des paiements, gestion des livraisons et traitement des retours. Il n'est cependant pas optimisé pour les analyses décisionnelles longues, les agrégations mensuelles ou les croisements par région, catégorie et client.

## Environnement MySQL retenu

Le compte `root` du MySQL système local n'était pas accessible. Pour garder un moteur MySQL réel sans modifier les données système Ubuntu, le projet utilise une instance MySQL dédiée :

- binaire serveur : `/usr/sbin/mysqld` ;
- dossier de données : `/tmp/mexora_mysql_project` ;
- hôte : `127.0.0.1` ;
- port : `3307` ;
- utilisateur projet : `mexora_user` ;
- base transactionnelle : `mexora_oltp` ;
- base décisionnelle : `mexora_dw`.

Le script `scripts/start_project_mysql.py` initialise et démarre cette instance lorsque `MEXORA_AUTO_START_MYSQL=1`. Le helper ne considère pas MySQL comme prêt sur un simple accès `root` : `mexora_user` doit se connecter en TCP à `127.0.0.1:3307` et ouvrir `mexora_oltp` et `mexora_dw`.

## Rôle de l'ETL

Le pipeline Python orchestre les étapes suivantes :

1. génération de données e-commerce marocaines ;
2. chargement de MySQL `mexora_oltp` ;
3. extraction des tables vers `data/raw/` ;
4. nettoyage et standardisation avec Pandas ;
5. construction des dimensions et de la table de faits ;
6. chargement du Data Warehouse MySQL `mexora_dw`.

L'ETL corrige ou isole les anomalies : emails invalides, villes incohérentes, statuts non standard, prix aberrants, quantités nulles, doublons et dates incohérentes.

## Rôle du Data Warehouse

La base MySQL `mexora_dw` est organisée en schéma en étoile :

- `fact_sales`
- `dim_customer`
- `dim_product`
- `dim_date`
- `dim_region`
- `dim_payment`
- `dim_delivery`

Ce modèle réduit la complexité des jointures, facilite les agrégations et rend les indicateurs plus lisibles pour les décideurs.

## Rôle de Metabase

Metabase est le dashboard BI final officiel du projet. Il se connecte directement au Data Warehouse MySQL `mexora_dw` et expose un dashboard `Mexora BI Dashboard` créé automatiquement via l'API Metabase.

Le dashboard couvre les cinq questions métier obligatoires du cahier de charge :

1. évolution du chiffre d'affaires par région ;
2. top produits trimestriels à Tanger ;
3. panier moyen par segment client ;
4. taux de retour par catégorie avec seuil d'alerte ;
5. effet Ramadan sur les ventes d'alimentation.

Streamlit reste disponible comme prototype Python complémentaire pour explorer localement les mêmes données. Power BI peut être envisagé comme amélioration future sous Windows pour une restitution plus corporate.

## Reporting matérialisé MySQL

Le cahier de charge recommande des vues matérialisées PostgreSQL. MySQL ne propose pas de `MATERIALIZED VIEW` native. Le projet fournit donc `sql/06_reporting_views_mysql.sql`, qui crée des tables de reporting rafraîchissables :

- `reporting_mv_ca_mensuel` ;
- `reporting_mv_top_produits` ;
- `reporting_mv_performance_livreurs`.

Ces tables sont construites par `CREATE TABLE AS SELECT` et indexées pour accélérer les analyses Metabase.

## Conformité académique au cahier de charge

Le cahier de charge demande également une structure ETL Python normalisée, des fichiers bruts spécifiques et des scripts PostgreSQL. Ces éléments sont fournis comme livrables académiques complémentaires :

- `data/academic_raw/commandes_mexora.csv` : 50 000 commandes imparfaites ;
- `data/academic_raw/produits_mexora.json` : catalogue produit brut ;
- `data/academic_raw/clients_mexora.csv` : clients bruts ;
- `data/academic_raw/regions_maroc.csv` : référentiel géographique propre ;
- `mexora_etl/` : package Python structuré selon l'énoncé ;
- `sql/postgres/` : implémentation PostgreSQL de référence avec schémas, index et vues matérialisées ;
- `sql/create_dwh.sql` et `sql/check_integrity.sql` : alias de livrables demandés ;
- `report/assets/schema_etoile_mexora.png` : schéma étoile annoté ;
- `docs/modeling_justification.pdf` et `docs/insights_metier.pdf` : documents PDF annexes.

Le moteur exécuté et validé reste MySQL isolé. Le choix est documenté, cohérent avec la source transactionnelle MySQL et acceptable dans le cadre de l'énoncé qui autorise les hypothèses techniques justifiées.
