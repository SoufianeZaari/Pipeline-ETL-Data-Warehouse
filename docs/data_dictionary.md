# Dictionnaire de données

## Tables OLTP MySQL - `mexora_oltp`

### customers

| Colonne | Type MySQL | Description |
|---|---|---|
| customer_id | INT | Identifiant naturel du client |
| full_name | VARCHAR(150) | Nom complet |
| email | VARCHAR(150) | Email, peut être invalide ou dupliqué avant nettoyage |
| phone | VARCHAR(30) | Téléphone |
| city | VARCHAR(80) | Ville saisie dans le système transactionnel |
| region | VARCHAR(120) | Région saisie |
| registration_date | DATE | Date d'inscription |
| gender | VARCHAR(20) | Genre |
| birth_date | DATE | Date de naissance |

### products

| Colonne | Type MySQL | Description |
|---|---|---|
| product_id | INT | Identifiant produit |
| product_name | VARCHAR(180) | Nom du produit |
| category | VARCHAR(60) | Electronics, Fashion ou Food |
| sub_category | VARCHAR(80) | Sous-catégorie |
| brand | VARCHAR(80) | Marque |
| supplier | VARCHAR(100) | Fournisseur |
| price | DECIMAL(10,2) | Prix catalogue, nettoyé ensuite si aberrant |
| created_at | DATE | Date de création |

### orders

| Colonne | Type MySQL | Description |
|---|---|---|
| order_id | INT | Identifiant commande |
| customer_id | INT | Référence vers `customers` |
| order_date | DATE | Date de commande |
| order_status | VARCHAR(30) | Statut transactionnel |
| total_amount | DECIMAL(12,2) | Montant source |

### order_items

| Colonne | Type MySQL | Description |
|---|---|---|
| order_item_id | INT | Identifiant de ligne |
| order_id | INT | Référence vers `orders` |
| product_id | INT | Référence vers `products` |
| quantity | INT | Quantité commandée |
| unit_price | DECIMAL(10,2) | Prix unitaire |
| discount_rate | DECIMAL(5,4) | Taux de remise |

### payments

| Colonne | Type MySQL | Description |
|---|---|---|
| payment_id | INT | Identifiant paiement |
| order_id | INT | Référence commande |
| payment_method | VARCHAR(50) | Méthode de paiement |
| payment_status | VARCHAR(40) | Statut de paiement |
| payment_date | DATE | Date de paiement |
| amount_paid | DECIMAL(12,2) | Montant payé |

### deliveries

| Colonne | Type MySQL | Description |
|---|---|---|
| delivery_id | INT | Identifiant livraison |
| order_id | INT | Référence commande |
| delivery_city | VARCHAR(80) | Ville de livraison |
| delivery_region | VARCHAR(120) | Région de livraison |
| delivery_status | VARCHAR(40) | Statut de livraison |
| shipping_company | VARCHAR(80) | Transporteur |
| shipped_date | DATE | Date d'expédition |
| delivered_date | DATE | Date de livraison |

### returns

| Colonne | Type MySQL | Description |
|---|---|---|
| return_id | INT | Identifiant retour |
| order_id | INT | Référence commande |
| product_id | INT | Produit retourné |
| return_reason | VARCHAR(120) | Raison du retour |
| return_date | DATE | Date du retour |
| refund_amount | DECIMAL(12,2) | Montant remboursé |

## Dimensions MySQL - `mexora_dw`

### dim_customer

| Colonne | Description |
|---|---|
| customer_key | Clé substitut |
| customer_id | Identifiant naturel |
| full_name | Nom complet |
| gender | Genre standardisé |
| age_group | Groupe d'âge |
| city | Ville standardisée |
| region | Région standardisée |
| segment_client | Segment client `Gold`, `Silver` ou `Bronze` calculé depuis le CA |
| registration_date | Date d'inscription |
| date_debut | Début de validité SCD |
| date_fin | Fin de validité SCD |
| est_actif | Indicateur de version active |

### dim_product

| Colonne | Description |
|---|---|
| product_key | Clé substitut |
| product_id | Identifiant naturel |
| product_name | Nom produit |
| category | Catégorie |
| sub_category | Sous-catégorie |
| brand | Marque |
| supplier | Fournisseur |
| date_debut | Début de validité SCD |
| date_fin | Fin de validité SCD |
| est_actif | Indicateur de version active |

### dim_date

| Colonne | Description |
|---|---|
| date_key | Clé `YYYYMMDD` |
| full_date | Date complète |
| day | Jour |
| month | Mois |
| month_name | Nom du mois |
| quarter | Trimestre |
| year | Année |
| is_weekend | Indicateur week-end |
| is_ramadan | Indicateur Ramadan 2026 |

### dim_region

| Colonne | Description |
|---|---|
| region_key | Clé substitut |
| city | Ville |
| region | Région |
| country | Pays |

### dim_payment

| Colonne | Description |
|---|---|
| payment_key | Clé substitut |
| payment_method | Méthode de paiement |
| payment_status | Statut de paiement |

### dim_delivery

| Colonne | Description |
|---|---|
| delivery_key | Clé substitut |
| delivery_status | Statut de livraison |
| shipping_company | Transporteur |
| delivery_city | Ville de livraison |
| delivery_region | Région de livraison |

### dim_livreur

Objet de compatibilité créé par `sql/06_reporting_views_mysql.sql`. Le cahier de charge demande une dimension livreur ; comme les données générées ne contiennent pas d'identifiant livreur individuel, le transporteur est utilisé comme proxy métier.

| Colonne | Description |
|---|---|
| id_livreur | Clé technique générée |
| nom_livreur | Nom du transporteur |
| type_transport | Type de transport |
| zone_couverture | Régions couvertes |

## Table de faits `fact_sales`

| Colonne | Description |
|---|---|
| sales_key | Clé substitut de la vente |
| order_id | Identifiant commande |
| order_item_id | Identifiant ligne de commande |
| customer_key | FK vers `dim_customer` |
| product_key | FK vers `dim_product` |
| date_key | FK vers `dim_date` |
| region_key | FK vers `dim_region` |
| payment_key | FK vers `dim_payment` |
| delivery_key | FK vers `dim_delivery` |
| quantity | Quantité vendue |
| unit_price | Prix unitaire |
| discount_rate | Taux de remise |
| total_amount | Montant après remise |
| amount_paid | Paiement alloué à la ligne |
| is_returned | 1 si retourné, 0 sinon |
| refund_amount | Montant remboursé |
| delivery_delay_days | Délai de livraison en jours |
| order_status | Statut commande standardisé |
| return_reason | Raison du retour |

## KPIs SQL et Metabase

| KPI | Définition |
|---|---|
| Chiffre d'affaires | `SUM(total_amount)` |
| Panier moyen | `SUM(total_amount) / COUNT(DISTINCT order_id)` |
| Taux de retour | `SUM(is_returned) / COUNT(*)` |
| Délai moyen de livraison | `AVG(delivery_delay_days)` |
| Montant remboursé | `SUM(refund_amount)` |
| Quantité vendue | `SUM(quantity)` |
| Nombre de commandes | `COUNT(DISTINCT order_id)` |
| Nombre de clients | `COUNT(DISTINCT customer_id)` |
| Panier moyen par segment | `SUM(total_amount) / COUNT(DISTINCT order_id)` groupé par `segment_client` |
| Seuil retour rouge | taux de retour catégorie `> 5 %` |
| Seuil retour orange | taux de retour catégorie entre `3 %` et `5 %` |
| Seuil retour vert | taux de retour catégorie `< 3 %` |

## Tables de reporting matérialisées MySQL

MySQL ne dispose pas de vues matérialisées natives. Le script `sql/06_reporting_views_mysql.sql` crée des tables de reporting rafraîchissables.

| Objet | Description |
|---|---|
| reporting_mv_ca_mensuel | CA mensuel par région et catégorie |
| reporting_mv_top_produits | Top produits par trimestre, catégorie et ville |
| reporting_mv_performance_livreurs | Performance des transporteurs/livreurs |

## Indicateurs affichés dans Metabase

Le dashboard final Metabase calcule et affiche notamment :

- chiffre d'affaires total ;
- nombre de commandes ;
- nombre de clients ;
- panier moyen ;
- taux de retour ;
- délai moyen de livraison ;
- montant remboursé ;
- quantité vendue ;
- chiffre d'affaires pendant Ramadan ;
- taux d'échec de livraison ;
- anomalies détectées, corrigées et supprimées.

Streamlit reste disponible comme prototype complémentaire dans `dashboard/streamlit_app.py`.

## Fichiers bruts académiques

Ces fichiers sont créés dans `data/academic_raw/` afin de correspondre aux données attendues par le cahier de charge.

### commandes_mexora.csv

| Colonne | Type logique | Description |
|---|---|---|
| id_commande | string | Identifiant brut de commande, avec doublons intentionnels |
| id_client | string | Clé naturelle client |
| id_produit | string | Clé naturelle produit |
| date_commande | string/date | Date brute en formats mixtes |
| quantite | numeric | Quantité commandée, avec valeurs invalides injectées |
| prix_unitaire | numeric | Prix unitaire, avec commandes test à prix 0 |
| statut | string | Statut brut : `livré`, `annulé`, `en_cours`, `retourné`, `OK`, `KO`, `DONE` |
| ville_livraison | string | Ville brute à standardiser avec `regions_maroc.csv` |
| mode_paiement | string | Méthode de paiement |
| id_livreur | string | Identifiant livreur, parfois manquant |
| date_livraison | string/date | Date brute de livraison |

### produits_mexora.json

| Colonne | Type logique | Description |
|---|---|---|
| id_produit | string | Identifiant naturel produit |
| nom | string | Libellé produit |
| categorie | string | Catégorie brute avec casse incohérente |
| sous_categorie | string | Sous-catégorie |
| marque | string | Marque |
| fournisseur | string | Fournisseur |
| prix_catalogue | numeric | Prix catalogue, parfois manquant |
| origine_pays | string | Pays d'origine |
| date_creation | date | Date de création |
| actif | boolean | Produit actif/inactif, utile pour la réflexion SCD |

### clients_mexora.csv

| Colonne | Type logique | Description |
|---|---|---|
| id_client | string | Identifiant naturel client |
| nom | string | Nom |
| prenom | string | Prénom |
| email | string | Email brut, parfois invalide ou dupliqué |
| date_naissance | string/date | Date utilisée pour la tranche d'âge |
| sexe | string | Codification hétérogène à normaliser |
| ville | string | Ville brute |
| telephone | string | Téléphone |
| date_inscription | string/date | Date d'inscription |
| canal_acquisition | string | Canal d'acquisition client |

### regions_maroc.csv

| Colonne | Type logique | Description |
|---|---|---|
| code_ville | string | Code court de ville |
| nom_ville_standard | string | Libellé ville normalisé |
| province | string | Province |
| region_admin | string | Région administrative |
| zone_geo | string | Zone géographique |
| population | integer | Population indicative |
| code_postal | string | Code postal principal |
