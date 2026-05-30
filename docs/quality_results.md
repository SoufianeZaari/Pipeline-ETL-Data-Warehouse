# Quality checks MySQL

Les contrôles qualité sont définis dans :

```text
sql/05_quality_checks.sql
```

Un alias de livrable demandé par le cahier de charge est également disponible :

```text
sql/check_integrity.sql
```

## Lancement

Après exécution du pipeline :

```bash
mysql -h 127.0.0.1 -P 3307 -u mexora_user -pmexora_pass mexora_dw < sql/05_quality_checks.sql
```

## Contrôles couverts

1. Nombre de lignes par dimension.
2. Nombre de lignes dans `fact_sales`.
3. Lignes avec `total_amount` négatif.
4. Lignes avec `quantity <= 0`.
5. `fact_sales` sans client correspondant.
6. `fact_sales` sans produit correspondant.
7. `fact_sales` sans date correspondante.
8. `fact_sales` sans région correspondante.
9. Nombre d'anomalies dans `quality_issues`.
10. Nombre de jours Ramadan dans `dim_date`.
11. Valeurs `Unknown` dans régions/villes.
12. Taux de retour global.
13. Délai moyen de livraison.

## Interprétation

Les compteurs d'anomalies doivent être lus avec `data/processed/quality_issues.csv` et `data/processed/transform_summary.json`. Une anomalie peut être :

- `corrected` : corrigée par une règle de transformation ;
- `removed` : supprimée ou isolée avant chargement dans la table de faits.

## Résultats validés

Dernière validation métier complète exécutée le 30 mai 2026 sur MySQL projet `127.0.0.1:3307`.

Le 30 mai 2026, les livrables académiques complémentaires ont été générés : fichiers bruts dans `data/academic_raw/`, schéma étoile en image, PDF de justification et PDF d'insights. La validation MySQL courante peut nécessiter de redémarrer proprement l'ancien processus MySQL projet si celui-ci garde des fichiers supprimés ouverts dans `/tmp`.

Volumes OLTP et table de faits :

| Table | Résultat |
|---|---:|
| `mexora_oltp.customers` | 1000 |
| `mexora_oltp.products` | 300 |
| `mexora_oltp.orders` | 5000 |
| `mexora_oltp.order_items` | 9424 |
| `mexora_oltp.payments` | 5000 |
| `mexora_oltp.deliveries` | 5000 |
| `mexora_oltp.returns` | 738 |
| `mexora_dw.fact_sales` | 9061 |

Dimensions et contrôles qualité :

| Table / contrôle | Résultat |
|---|---:|
| `dim_customer` | 1000 |
| `dim_product` | 300 |
| `dim_date` | 704 |
| `dim_region` | 20 |
| `dim_payment` | 17 |
| `dim_delivery` | 309 |
| `fact_sales` | 9061 |
| Montants négatifs dans `fact_sales` | 0 |
| Quantités invalides dans `fact_sales` | 0 |
| Faits sans client | 0 |
| Faits sans produit | 0 |
| Faits sans date | 0 |
| Faits sans région | 0 |
| Jours Ramadan dans `dim_date` | 30 |
| Lignes retournées | 713 |
| Taux de retour global | 7.87 % |
| Délai moyen de livraison | 14.99 jours |

Répartition des anomalies chargées dans `quality_issues` :

| Table source | Action | Nombre |
|---|---|---:|
| deliveries | corrected | 737 |
| order_items | removed | 363 |
| payments | corrected | 309 |
| customers | corrected | 145 |
| products | corrected | 5 |

Valeurs géographiques `Unknown` conservées après application des règles métier :

| Dimension | Lignes |
|---|---:|
| `dim_customer` | 43 |
| `dim_region` | 8 |
| `dim_delivery` | 76 |

Tables de reporting rafraîchissables :

| Objet | Lignes |
|---|---:|
| `dim_livreur` | 6 |
| `reporting_mv_ca_mensuel` | 465 |
| `reporting_mv_top_produits` | 6022 |
| `reporting_mv_performance_livreurs` | 640 |
