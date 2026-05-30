# Guide de connexion Power BI à MySQL - amélioration future

Le dashboard final officiel du rendu Linux est Metabase. Ce guide Power BI est conservé comme amélioration future possible sous Windows.

## Pré-requis

- MySQL Server démarré localement.
- Base `mexora_dw` créée et chargée par le pipeline ETL.
- Connecteur MySQL disponible dans Power BI Desktop.

## Connexion

1. Ouvrir Power BI Desktop.
2. Cliquer sur **Get Data**.
3. Choisir **MySQL database**.
4. Renseigner :
   - Server : `localhost`
   - Database : `mexora_dw`
5. Choisir le mode **Import**.
6. Importer les tables :
   - `fact_sales`
   - `dim_customer`
   - `dim_product`
   - `dim_date`
   - `dim_region`
   - `dim_payment`
   - `dim_delivery`
7. Cliquer sur **Load**.

## Relations à créer

Créer les relations suivantes dans la vue modèle :

- `fact_sales.customer_key` -> `dim_customer.customer_key`
- `fact_sales.product_key` -> `dim_product.product_key`
- `fact_sales.date_key` -> `dim_date.date_key`
- `fact_sales.region_key` -> `dim_region.region_key`
- `fact_sales.payment_key` -> `dim_payment.payment_key`
- `fact_sales.delivery_key` -> `dim_delivery.delivery_key`

Toutes les relations doivent être en cardinalité `Many-to-One`, avec filtre simple depuis les dimensions vers la table de faits.

## Mesures DAX

Créer les mesures listées dans `dashboard/powerbi/measures.dax`.

## Fichier PBIX

Le fichier `.pbix` ne peut pas être généré de manière fiable sans Power BI Desktop sur la machine. Il doit être créé manuellement en suivant ce guide, puis ajouté dans ce dossier sous le nom :

```text
dashboard/powerbi/mexora_dashboard.pbix
```
