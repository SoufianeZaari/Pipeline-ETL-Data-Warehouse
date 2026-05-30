# Modèle Power BI - amélioration future

Le dashboard final officiel du rendu Linux est `dashboard/streamlit_app.py`.

Ce dossier Power BI est conservé comme amélioration future possible sous Windows, pour une restitution corporate à partir du même Data Warehouse MySQL `mexora_dw`.

## Tables à importer

- `fact_sales`
- `dim_customer`
- `dim_product`
- `dim_date`
- `dim_region`
- `dim_payment`
- `dim_delivery`

La table `quality_issues` peut être importée dans une page technique optionnelle, mais elle n'est pas nécessaire pour les pages décisionnelles principales.

## Relations

| Table de faits | Dimension | Cardinalité | Sens de filtre |
|---|---|---|---|
| `fact_sales.customer_key` | `dim_customer.customer_key` | Many-to-One | Single |
| `fact_sales.product_key` | `dim_product.product_key` | Many-to-One | Single |
| `fact_sales.date_key` | `dim_date.date_key` | Many-to-One | Single |
| `fact_sales.region_key` | `dim_region.region_key` | Many-to-One | Single |
| `fact_sales.payment_key` | `dim_payment.payment_key` | Many-to-One | Single |
| `fact_sales.delivery_key` | `dim_delivery.delivery_key` | Many-to-One | Single |

## Recommandations de modélisation

- Marquer `dim_date` comme table de dates en utilisant la colonne `full_date`.
- Masquer les clés techniques dans les vues de rapport lorsque les utilisateurs métier n'en ont pas besoin.
- Formater les montants en MAD.
- Formater `Taux Retour` en pourcentage.
- Utiliser `dim_date[year]`, `dim_date[quarter]`, `dim_date[month]` et `dim_date[month_name]` pour les analyses temporelles.
- Utiliser `dim_date[is_ramadan]` pour filtrer les performances pendant Ramadan 2026.
