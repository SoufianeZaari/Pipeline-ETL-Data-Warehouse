-- ============================================================
-- Mexora BI Project
-- Requêtes analytiques MySQL sur le Data Warehouse
-- ============================================================

USE mexora_dw;

-- 1. Top 10 meilleurs clients à Tanger sur le trimestre le plus récent chargé.
WITH latest_period AS (
    SELECT year, quarter
    FROM dim_date
    ORDER BY full_date DESC
    LIMIT 1
)
SELECT
    c.customer_id,
    c.full_name,
    c.city,
    d.year,
    d.quarter,
    COUNT(DISTINCT f.order_id) AS nb_commandes,
    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires
FROM fact_sales f
JOIN dim_customer c ON f.customer_key = c.customer_key
JOIN dim_date d ON f.date_key = d.date_key
JOIN latest_period lp ON d.year = lp.year AND d.quarter = lp.quarter
WHERE c.city = 'Tanger'
GROUP BY c.customer_id, c.full_name, c.city, d.year, d.quarter
ORDER BY chiffre_affaires DESC
LIMIT 10;

-- 2. Chiffre d'affaires par mois.
SELECT
    d.year,
    d.month,
    d.month_name,
    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;

-- 3. Chiffre d'affaires par région.
SELECT
    r.region,
    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires,
    COUNT(DISTINCT f.order_id) AS nb_commandes
FROM fact_sales f
JOIN dim_region r ON f.region_key = r.region_key
GROUP BY r.region
ORDER BY chiffre_affaires DESC;

-- 4. Catégorie la plus performante pendant Ramadan.
SELECT
    p.category,
    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires_ramadan,
    SUM(f.quantity) AS quantite_vendue
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
JOIN dim_date d ON f.date_key = d.date_key
WHERE d.is_ramadan = 1
GROUP BY p.category
ORDER BY chiffre_affaires_ramadan DESC
LIMIT 1;

-- 5. Taux de retour par région.
SELECT
    r.region,
    COUNT(*) AS lignes_vente,
    SUM(f.is_returned) AS lignes_retournees,
    ROUND(100.0 * SUM(f.is_returned) / NULLIF(COUNT(*), 0), 2) AS taux_retour_pct
FROM fact_sales f
JOIN dim_region r ON f.region_key = r.region_key
GROUP BY r.region
ORDER BY taux_retour_pct DESC;

-- 6. Panier moyen par mois.
SELECT
    d.year,
    d.month,
    d.month_name,
    ROUND(SUM(f.total_amount) / NULLIF(COUNT(DISTINCT f.order_id), 0), 2) AS panier_moyen
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;

-- 7. Top 10 produits les plus vendus.
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(f.quantity) AS quantite_totale,
    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.product_id, p.product_name, p.category
ORDER BY quantite_totale DESC, chiffre_affaires DESC
LIMIT 10;

-- 8. Top 10 produits les plus retournés.
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(f.is_returned) AS nb_retours,
    ROUND(SUM(f.refund_amount), 2) AS montant_rembourse
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.product_id, p.product_name, p.category
HAVING nb_retours > 0
ORDER BY nb_retours DESC, montant_rembourse DESC
LIMIT 10;

-- 9. Délai moyen de livraison par région.
SELECT
    r.region,
    ROUND(AVG(f.delivery_delay_days), 2) AS delai_moyen_jours
FROM fact_sales f
JOIN dim_region r ON f.region_key = r.region_key
WHERE f.delivery_delay_days IS NOT NULL
GROUP BY r.region
ORDER BY delai_moyen_jours DESC;

-- 10. Répartition des paiements par méthode.
SELECT
    p.payment_method,
    COUNT(DISTINCT f.order_id) AS nb_commandes,
    ROUND(SUM(f.amount_paid), 2) AS montant_paye
FROM fact_sales f
JOIN dim_payment p ON f.payment_key = p.payment_key
GROUP BY p.payment_method
ORDER BY nb_commandes DESC;

-- 11. Taux d'échec de livraison par transporteur.
SELECT
    d.shipping_company,
    COUNT(*) AS lignes_livraison,
    SUM(CASE WHEN d.delivery_status = 'failed' THEN 1 ELSE 0 END) AS echecs,
    ROUND(100.0 * SUM(CASE WHEN d.delivery_status = 'failed' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS taux_echec_pct
FROM fact_sales f
JOIN dim_delivery d ON f.delivery_key = d.delivery_key
GROUP BY d.shipping_company
ORDER BY taux_echec_pct DESC;

-- 12. Nombre de commandes par statut.
SELECT
    order_status,
    COUNT(DISTINCT order_id) AS nb_commandes
FROM fact_sales
GROUP BY order_status
ORDER BY nb_commandes DESC;

-- 13. Chiffre d'affaires par catégorie et trimestre.
SELECT
    d.year,
    d.quarter,
    p.category,
    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY d.year, d.quarter, p.category
ORDER BY d.year, d.quarter, chiffre_affaires DESC;

-- 14. Chiffre d'affaires par ville.
SELECT
    r.city,
    r.region,
    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires
FROM fact_sales f
JOIN dim_region r ON f.region_key = r.region_key
GROUP BY r.city, r.region
ORDER BY chiffre_affaires DESC;

-- 15. Taux de retour par catégorie de produit.
SELECT
    p.category,
    COUNT(*) AS lignes_vente,
    SUM(f.is_returned) AS lignes_retournees,
    ROUND(100.0 * SUM(f.is_returned) / NULLIF(COUNT(*), 0), 2) AS taux_retour_pct
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.category
ORDER BY taux_retour_pct DESC;

-- 16. Cahier de charge - évolution mensuelle du CA par région.
SELECT
    DATE_FORMAT(d.full_date, '%Y-%m') AS mois,
    r.region,
    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
JOIN dim_region r ON f.region_key = r.region_key
WHERE f.order_status IN ('completed', 'returned')
GROUP BY DATE_FORMAT(d.full_date, '%Y-%m'), r.region
ORDER BY mois, chiffre_affaires DESC;

-- 17. Cahier de charge - top 10 produits vendus par trimestre à Tanger.
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
ORDER BY d.year DESC, d.quarter DESC, chiffre_affaires DESC
LIMIT 10;

-- 18. Cahier de charge - panier moyen par segment client.
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

-- 19. Cahier de charge - taux de retour par catégorie avec seuil d'alerte.
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

-- 20. Cahier de charge - effet Ramadan sur l'alimentation.
SELECT
    CASE WHEN d.is_ramadan = 1 THEN 'Ramadan' ELSE 'Hors Ramadan' END AS periode,
    ROUND(SUM(f.total_amount), 2) AS chiffre_affaires,
    SUM(f.quantity) AS volume_vendu,
    ROUND(AVG(f.total_amount), 2) AS panier_ligne_moyen
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
JOIN dim_date d ON f.date_key = d.date_key
WHERE p.category = 'Food'
  AND f.order_status IN ('completed', 'returned')
GROUP BY CASE WHEN d.is_ramadan = 1 THEN 'Ramadan' ELSE 'Hors Ramadan' END
ORDER BY chiffre_affaires DESC;
