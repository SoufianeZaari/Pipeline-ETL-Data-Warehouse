-- ============================================================
-- Mexora BI Project
-- Contrôles qualité MySQL sur le Data Warehouse mexora_dw
-- ============================================================

USE mexora_dw;

-- 1. Nombre de lignes par dimension.
SELECT 'dim_customer' AS table_name, COUNT(*) AS row_count FROM dim_customer
UNION ALL SELECT 'dim_product', COUNT(*) FROM dim_product
UNION ALL SELECT 'dim_date', COUNT(*) FROM dim_date
UNION ALL SELECT 'dim_region', COUNT(*) FROM dim_region
UNION ALL SELECT 'dim_payment', COUNT(*) FROM dim_payment
UNION ALL SELECT 'dim_delivery', COUNT(*) FROM dim_delivery;

-- 2. Nombre de lignes dans fact_sales.
SELECT COUNT(*) AS fact_sales_rows
FROM fact_sales;

-- 3. Lignes avec total_amount négatif.
SELECT COUNT(*) AS negative_total_amount_rows
FROM fact_sales
WHERE total_amount < 0;

-- 4. Lignes avec quantity <= 0.
SELECT COUNT(*) AS invalid_quantity_rows
FROM fact_sales
WHERE quantity <= 0;

-- 5. fact_sales sans client correspondant.
SELECT COUNT(*) AS fact_without_customer
FROM fact_sales f
LEFT JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE c.customer_key IS NULL;

-- 6. fact_sales sans produit correspondant.
SELECT COUNT(*) AS fact_without_product
FROM fact_sales f
LEFT JOIN dim_product p ON f.product_key = p.product_key
WHERE p.product_key IS NULL;

-- 7. fact_sales sans date correspondante.
SELECT COUNT(*) AS fact_without_date
FROM fact_sales f
LEFT JOIN dim_date d ON f.date_key = d.date_key
WHERE d.date_key IS NULL;

-- 8. fact_sales sans région correspondante.
SELECT COUNT(*) AS fact_without_region
FROM fact_sales f
LEFT JOIN dim_region r ON f.region_key = r.region_key
WHERE r.region_key IS NULL;

-- 9. Nombre d'anomalies chargées dans quality_issues.
SELECT
    table_name,
    action,
    COUNT(*) AS nb_anomalies
FROM quality_issues
GROUP BY table_name, action
ORDER BY nb_anomalies DESC;

-- 10. Nombre de jours Ramadan dans dim_date.
SELECT
    MIN(full_date) AS debut_ramadan,
    MAX(full_date) AS fin_ramadan,
    COUNT(*) AS nb_jours_ramadan
FROM dim_date
WHERE is_ramadan = 1;

-- 11. Valeurs Unknown dans les régions/villes.
SELECT 'dim_customer' AS table_name, COUNT(*) AS unknown_geo_rows
FROM dim_customer
WHERE city = 'Unknown' OR region = 'Unknown'
UNION ALL
SELECT 'dim_region', COUNT(*)
FROM dim_region
WHERE city = 'Unknown' OR region = 'Unknown'
UNION ALL
SELECT 'dim_delivery', COUNT(*)
FROM dim_delivery
WHERE delivery_city = 'Unknown' OR delivery_region = 'Unknown';

-- 12. Taux de retour global.
SELECT
    COUNT(*) AS lignes_vente,
    SUM(is_returned) AS lignes_retournees,
    ROUND(100 * SUM(is_returned) / NULLIF(COUNT(*), 0), 2) AS taux_retour_pct
FROM fact_sales;

-- 13. Délai moyen de livraison.
SELECT
    ROUND(AVG(delivery_delay_days), 2) AS delai_moyen_livraison_jours
FROM fact_sales
WHERE delivery_delay_days IS NOT NULL;
