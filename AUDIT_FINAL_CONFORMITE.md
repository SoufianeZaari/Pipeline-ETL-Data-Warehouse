# Audit final de conformité - Mini-Projet 1 Mexora Analytics

Date de contrôle : 30 mai 2026

Architecture défendue :

```text
MySQL OLTP isolé 127.0.0.1:3307
-> ETL Python
-> MySQL Data Warehouse mexora_dw
-> SQL Analytics
-> Metabase BI Dashboard
-> Rapport PDF + GitHub
```

## A. Conformité Étape 1 - Modélisation

Statut : conforme avec justification.

Preuves :

- schéma étoile : `report/assets/schema_etoile_mexora.png` ;
- justification : `docs/modeling_justification.md` et `docs/modeling_justification.pdf` ;
- dictionnaire : `docs/data_dictionary.md` ;
- rapport final : `report/rapport_mexora.md`.

Corrections appliquées :

- granularité explicitée : une ligne de fait représente une ligne de commande vendue ;
- dimension livreur documentée via `dim_livreur`, construite depuis les transporteurs ;
- tableau d'additivité ajouté dans le rapport ;
- SCD Type 1 et SCD Type 2 documentés sans prétendre une historisation multi-version complète.

Risques restants : faible. Le SCD Type 2 est SCD-ready mais pas alimenté en historique multi-version automatisé.

## B. Conformité Étape 2 - ETL Python

Statut : conforme.

Preuves :

- pipeline validé : `scripts/run_etl.py` ;
- extraction MySQL : `scripts/extract.py` ;
- transformations : `scripts/transform.py` ;
- chargement DW : `scripts/load.py` ;
- structure académique : `mexora_etl/`.

Corrections appliquées :

- fichiers bruts académiques présents dans `data/academic_raw/` ;
- rapport des transformations enrichi avec les volumes et règles ;
- façade `mexora_etl/transform/clean_produits.py` renforcée pour produits inactifs et colonnes SCD-ready.

Risques restants : très faible. Le pipeline opérationnel validé reste celui de `scripts/`.

## C. Conformité Étape 3 - PostgreSQL / SQL DWH

Statut : conforme sur le plan académique, exécution locale validée en MySQL.

Preuves :

- MySQL DW exécutable : `sql/03_dw_schema.sql` ;
- contrôles MySQL : `sql/05_quality_checks.sql` ;
- reporting MySQL : `sql/06_reporting_views_mysql.sql` ;
- PostgreSQL de référence : `sql/postgres/01_create_dwh.sql`, `sql/postgres/02_check_integrity.sql`, `sql/postgres/03_reporting_materialized_views.sql`.

Corrections appliquées :

- section "Conformité PostgreSQL" ajoutée au rapport ;
- explication claire : PostgreSQL est fourni en scripts conformes, MySQL isolé est la chaîne démontrée ;
- vues matérialisées PostgreSQL et tables de reporting MySQL documentées.

Risques restants : moyen-faible si l'enseignant exige une exécution PostgreSQL réelle. Le risque est réduit par les scripts PostgreSQL complets.

## D. Conformité Étape 4 - Dashboard

Statut : conforme avec tâche manuelle finale pour captures.

Preuves :

- guide Metabase : `metabase/README_metabase.md` ;
- plan dashboard : `metabase/dashboard_plan.md` ;
- SQL des questions : `metabase/questions_sql.md` ;
- automatisation API : `metabase/create_mexora_dashboard.py`.

Corrections appliquées :

- les cinq questions obligatoires sont couvertes ;
- Q1 inclut l'évolution mensuelle par région avec comparaison à la période précédente ;
- Q5 inclut l'effet Ramadan Food avec indice de performance ;
- méthode manuelle documentée si l'API Metabase est instable.

Risques restants : moyen tant que les captures Metabase réelles ne sont pas insérées dans le rapport. Lors de la validation, l'API Metabase a créé ou mis à jour les questions, mais le placement automatique de certaines cartes peut échouer si le stockage interne Metabase signale une erreur `REPORT_DASHBOARDCARD`. La méthode manuelle de secours est documentée.

## E. Livrables finaux L1 à L8

| Livrable | Existe | Chemin | Statut | Action restante |
|---|---|---|---|---|
| L1 Schéma ER annoté | Oui | `report/assets/schema_etoile_mexora.png`, `docs/er_schema_mexora.mmd` | conforme | aucune |
| L2 Document justification PDF | Oui | `docs/modeling_justification.pdf` | conforme | aucune |
| L3 Code Python ETL dépôt Git | Oui | `scripts/`, `mexora_etl/` | conforme | publier sur GitHub |
| L4 Rapport transformations Markdown | Oui | `docs/rapport_transformations.md` | conforme | aucune |
| L5 Scripts SQL création DWH | Oui | `sql/03_dw_schema.sql`, `sql/create_dwh.sql`, `sql/postgres/01_create_dwh.sql` | conforme | aucune |
| L6 Script intégrité | Oui | `sql/05_quality_checks.sql`, `sql/check_integrity.sql`, `sql/postgres/02_check_integrity.sql` | conforme | aucune |
| L7 Dashboard Metabase | Oui | `metabase/create_mexora_dashboard.py`, `metabase/questions_sql.md` | conforme | créer/valider les cartes dans Metabase et prendre captures |
| L8 Document insights PDF | Oui | `docs/insights_metier.pdf` | conforme | régénéré si modification des données |

## F. Commandes finales de rendu

```bash
cd "/home/soufiane/DATAEng/Miniprojet 1/mexora-bi-project"
source .venv/bin/activate

python scripts/start_project_mysql.py
python scripts/run_etl.py --regenerate

mysql -h 127.0.0.1 -P 3307 -u mexora_user -pmexora_pass mexora_dw < sql/04_analytics_queries.sql
mysql -h 127.0.0.1 -P 3307 -u mexora_user -pmexora_pass mexora_dw < sql/05_quality_checks.sql
mysql -h 127.0.0.1 -P 3307 -u mexora_user -pmexora_pass mexora_dw < sql/06_reporting_views_mysql.sql

bash metabase/start_metabase.sh
python metabase/create_mexora_dashboard.py
```

## G. Tâches manuelles restantes

- publier le dépôt sur GitHub et remplacer `Repository GitHub : à compléter` ;
- ouvrir Metabase, vérifier le dashboard et insérer les captures réelles ;
- si l'API Metabase reste instable, créer les cartes manuellement depuis `metabase/questions_sql.md`.

## H. Risque de perte de points

Estimation : faible à moyen.

Les éléments techniques majeurs sont présents. Le principal risque porte sur l'exigence PostgreSQL si l'enseignant exige une exécution réelle, et sur les captures Metabase à insérer manuellement avant rendu.
