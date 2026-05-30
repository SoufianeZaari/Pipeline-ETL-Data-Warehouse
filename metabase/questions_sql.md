# Questions SQL Metabase - Mexora BI Dashboard

## KPI - Chiffre d'affaires total

```sql
SELECT ROUND(SUM(total_amount), 2) AS chiffre_affaires_total
FROM fact_sales;
```

## KPI - Nombre de commandes

```sql
SELECT COUNT(DISTINCT order_id) AS nombre_commandes
FROM fact_sales;
```

## KPI - Panier moyen

```sql
SELECT ROUND(SUM(total_amount) / COUNT(DISTINCT order_id), 2) AS panier_moyen
FROM fact_sales;
```

## KPI - Taux de retour global

```sql
SELECT ROUND(SUM(is_returned) * 100.0 / COUNT(*), 2) AS taux_retour_global
FROM fact_sales;
```

## KPI - Délai moyen livraison

```sql
SELECT ROUND(AVG(delivery_delay_days), 2) AS delai_moyen_livraison
FROM fact_sales;
```

## KPI - Montant remboursé total

```sql
SELECT ROUND(SUM(refund_amount), 2) AS montant_rembourse_total
FROM fact_sales;
```

## Chiffre d'affaires par mois

```sql
SELECT 
    DATE_FORMAT(d.full_date, '%Y-%m') AS mois,
    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY DATE_FORMAT(d.full_date, '%Y-%m')
ORDER BY mois;
```

## Chiffre d'affaires par région

```sql
SELECT 
    r.region,
    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires
FROM fact_sales f
JOIN dim_region r ON f.region_key = r.region_key
GROUP BY r.region
ORDER BY chiffre_affaires DESC;
```

## Chiffre d'affaires par catégorie

```sql
SELECT 
    p.category,
    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.category
ORDER BY chiffre_affaires DESC;
```

## Chiffre d'affaires par ville

```sql
SELECT 
    r.city,
    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires
FROM fact_sales f
JOIN dim_region r ON f.region_key = r.region_key
GROUP BY r.city
ORDER BY chiffre_affaires DESC;
```

## Top 10 clients

```sql
SELECT 
    c.full_name,
    c.city,
    ROUND(SUM(f.total_amount), 2) AS total_depense
FROM fact_sales f
JOIN dim_customer c ON f.customer_key = c.customer_key
GROUP BY c.full_name, c.city
ORDER BY total_depense DESC
LIMIT 10;
```

## Top 10 clients à Tanger

```sql
SELECT 
    c.full_name,
    ROUND(SUM(f.total_amount), 2) AS total_depense
FROM fact_sales f
JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE c.city = 'Tanger'
GROUP BY c.full_name
ORDER BY total_depense DESC
LIMIT 10;
```

## Nombre de clients par région

```sql
SELECT 
    region,
    COUNT(DISTINCT customer_id) AS nombre_clients
FROM dim_customer
GROUP BY region
ORDER BY nombre_clients DESC;
```

## Panier moyen par région

```sql
SELECT 
    r.region,
    ROUND(SUM(f.total_amount) / COUNT(DISTINCT f.order_id), 2) AS panier_moyen
FROM fact_sales f
JOIN dim_region r ON f.region_key = r.region_key
GROUP BY r.region
ORDER BY panier_moyen DESC;
```

## Top produits vendus

```sql
SELECT 
    p.product_name,
    p.category,
    SUM(f.quantity) AS quantite_vendue,
    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.product_name, p.category
ORDER BY quantite_vendue DESC
LIMIT 10;
```

## Produits les plus retournés

```sql
SELECT 
    p.product_name,
    p.category,
    SUM(f.is_returned) AS total_retours
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.product_name, p.category
ORDER BY total_retours DESC
LIMIT 10;
```

## Performance catégorie pendant Ramadan

```sql
SELECT 
    p.category,
    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires_ramadan
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
JOIN dim_date d ON f.date_key = d.date_key
WHERE d.is_ramadan = 1
GROUP BY p.category
ORDER BY chiffre_affaires_ramadan DESC;
```

## Quantité vendue par catégorie

```sql
SELECT 
    p.category,
    SUM(f.quantity) AS quantite_vendue
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.category
ORDER BY quantite_vendue DESC;
```

## Taux de retour par région

```sql
SELECT 
    r.region,
    ROUND(SUM(f.is_returned) * 100.0 / COUNT(*), 2) AS taux_retour
FROM fact_sales f
JOIN dim_region r ON f.region_key = r.region_key
GROUP BY r.region
ORDER BY taux_retour DESC;
```

## Délai moyen livraison par région

```sql
SELECT 
    r.region,
    ROUND(AVG(f.delivery_delay_days), 2) AS delai_moyen_livraison
FROM fact_sales f
JOIN dim_region r ON f.region_key = r.region_key
WHERE f.delivery_delay_days IS NOT NULL
GROUP BY r.region
ORDER BY delai_moyen_livraison DESC;
```

## Statuts de livraison

```sql
SELECT 
    d.delivery_status,
    COUNT(*) AS total
FROM fact_sales f
JOIN dim_delivery d ON f.delivery_key = d.delivery_key
GROUP BY d.delivery_status
ORDER BY total DESC;
```

## Répartition des paiements

```sql
SELECT 
    p.payment_method,
    COUNT(*) AS total
FROM fact_sales f
JOIN dim_payment p ON f.payment_key = p.payment_key
GROUP BY p.payment_method
ORDER BY total DESC;
```

## Anomalies par type

```sql
SELECT 
    issue_type,
    COUNT(*) AS total
FROM quality_issues
GROUP BY issue_type
ORDER BY total DESC;
```

## Résumé qualité des données

```sql
SELECT 'Anomalies détectées' AS indicateur, COUNT(*) AS valeur
FROM quality_issues
UNION ALL
SELECT 'Montants négatifs dans fact_sales', COUNT(*)
FROM fact_sales
WHERE total_amount < 0
UNION ALL
SELECT 'Quantités invalides dans fact_sales', COUNT(*)
FROM fact_sales
WHERE quantity <= 0
UNION ALL
SELECT 'Faits sans customer', COUNT(*)
FROM fact_sales f
LEFT JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE c.customer_key IS NULL;
```

## Cahier - Evolution CA mensuelle par région

```sql
WITH bornes AS (
    SELECT MAX(d.full_date) AS max_date
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
), ca_region_mois AS (
    SELECT
        DATE_FORMAT(d.full_date, '%Y-%m') AS mois,
        r.region,
        ROUND(SUM(f.total_amount), 2) AS chiffre_affaires
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    JOIN dim_region r ON f.region_key = r.region_key
    CROSS JOIN bornes b
    WHERE f.order_status IN ('completed', 'returned')
      AND d.full_date >= DATE_SUB(b.max_date, INTERVAL 12 MONTH)
    GROUP BY DATE_FORMAT(d.full_date, '%Y-%m'), r.region
)
SELECT
    mois,
    region,
    chiffre_affaires,
    RANK() OVER (PARTITION BY mois ORDER BY chiffre_affaires DESC) AS rang_region_mois,
    LAG(chiffre_affaires) OVER (PARTITION BY region ORDER BY mois) AS ca_mois_precedent,
    ROUND(
        (chiffre_affaires - LAG(chiffre_affaires) OVER (PARTITION BY region ORDER BY mois))
        * 100.0 / NULLIF(LAG(chiffre_affaires) OVER (PARTITION BY region ORDER BY mois), 0),
        2
    ) AS evolution_pct
FROM ca_region_mois
ORDER BY mois, rang_region_mois, chiffre_affaires DESC;
```

## Cahier - Top produits trimestriels à Tanger

```sql
WITH ventes_tanger AS (
    SELECT
        d.year,
        d.quarter,
        p.product_name,
        p.category,
        SUM(f.quantity) AS quantite_vendue,
        ROUND(SUM(f.total_amount), 2) AS chiffre_affaires
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    JOIN dim_product p ON f.product_key = p.product_key
    JOIN dim_region r ON f.region_key = r.region_key
    WHERE r.city = 'Tanger'
      AND f.order_status IN ('completed', 'returned')
    GROUP BY d.year, d.quarter, p.product_name, p.category
), ranked AS (
    SELECT
        ventes_tanger.*,
        ROW_NUMBER() OVER (PARTITION BY year, quarter ORDER BY chiffre_affaires DESC, quantite_vendue DESC) AS rang_trimestre
    FROM ventes_tanger
)
SELECT
    year,
    quarter,
    rang_trimestre,
    product_name,
    category,
    quantite_vendue,
    chiffre_affaires
FROM ranked
WHERE rang_trimestre <= 10
ORDER BY year DESC, quarter DESC, rang_trimestre;
```

## Cahier - Panier moyen par segment client

```sql
SELECT
    c.segment_client,
    COUNT(DISTINCT f.order_id) AS nb_commandes,
    ROUND(SUM(f.total_amount) / NULLIF(COUNT(DISTINCT f.order_id), 0), 2) AS panier_moyen,
    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires
FROM fact_sales f
JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE f.order_status IN ('completed', 'returned')
GROUP BY c.segment_client
ORDER BY panier_moyen DESC;
```

## Cahier - Taux retour catégorie avec alerte

```sql
SELECT
    p.category,
    SUM(f.is_returned) AS nb_retours,
    COUNT(*) AS nb_lignes,
    ROUND(SUM(f.is_returned) * 100.0 / NULLIF(COUNT(*), 0), 2) AS taux_retour_pct,
    CASE
        WHEN SUM(f.is_returned) * 100.0 / NULLIF(COUNT(*), 0) > 5 THEN 'Rouge'
        WHEN SUM(f.is_returned) * 100.0 / NULLIF(COUNT(*), 0) >= 3 THEN 'Orange'
        ELSE 'Vert'
    END AS niveau_alerte
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.category
ORDER BY taux_retour_pct DESC;
```

## Cahier - Effet Ramadan alimentation

```sql
WITH ventes_food_jour AS (
    SELECT
        d.full_date,
        d.is_ramadan,
        ROUND(SUM(f.total_amount), 2) AS ca_journalier,
        SUM(f.quantity) AS volume_journalier
    FROM fact_sales f
    JOIN dim_product p ON f.product_key = p.product_key
    JOIN dim_date d ON f.date_key = d.date_key
    WHERE p.category = 'Food'
      AND f.order_status IN ('completed', 'returned')
    GROUP BY d.full_date, d.is_ramadan
), synthese AS (
    SELECT
        CASE WHEN is_ramadan = 1 THEN 'Ramadan' ELSE 'Hors Ramadan' END AS periode,
        ROUND(SUM(ca_journalier), 2) AS chiffre_affaires,
        SUM(volume_journalier) AS volume_vendu,
        ROUND(AVG(ca_journalier), 2) AS ca_moyen_journalier
    FROM ventes_food_jour
    GROUP BY is_ramadan
), reference AS (
    SELECT ca_moyen_journalier AS ca_moyen_hors_ramadan
    FROM synthese
    WHERE periode = 'Hors Ramadan'
)
SELECT
    s.periode,
    s.chiffre_affaires,
    s.volume_vendu,
    s.ca_moyen_journalier,
    ROUND(s.ca_moyen_journalier * 100.0 / NULLIF(r.ca_moyen_hors_ramadan, 0), 2) AS indice_performance_ramadan
FROM synthese s
CROSS JOIN reference r
ORDER BY s.periode DESC;
```
