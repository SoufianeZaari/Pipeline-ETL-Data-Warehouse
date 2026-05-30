-- ============================================================
-- Mexora BI Project
-- Tables de reporting matérialisées compatibles MySQL
-- Base: mexora_dw
-- ============================================================
--
-- Le cahier de charge recommande PostgreSQL et des MATERIALIZED VIEW.
-- MySQL ne fournit pas de MATERIALIZED VIEW native. Pour conserver
-- l'architecture MySQL validée, ce script crée des tables de reporting
-- rafraîchissables avec DROP + CREATE TABLE AS SELECT, puis ajoute les index.
-- ============================================================

USE mexora_dw;

-- Dimension livreur logique.
-- Les données générées ne contiennent pas d'id_livreur individuel.
-- Le transporteur de dim_delivery joue donc le rôle métier du livreur.
DROP VIEW IF EXISTS dim_livreur;
DROP TABLE IF EXISTS dim_livreur;

CREATE TABLE dim_livreur AS
SELECT
    ROW_NUMBER() OVER (ORDER BY shipping_company) AS id_livreur,
    shipping_company AS nom_livreur,
    'Transporteur partenaire' AS type_transport,
    GROUP_CONCAT(DISTINCT delivery_region ORDER BY delivery_region SEPARATOR ', ') AS zone_couverture
FROM dim_delivery
GROUP BY shipping_company;

ALTER TABLE dim_livreur
    MODIFY id_livreur BIGINT NOT NULL,
    ADD PRIMARY KEY (id_livreur),
    ADD INDEX idx_dim_livreur_nom (nom_livreur);

-- Vue matérialisée simulée 1 : CA mensuel par région et catégorie.
DROP TABLE IF EXISTS reporting_mv_ca_mensuel;

CREATE TABLE reporting_mv_ca_mensuel AS
SELECT
    d.year AS annee,
    d.month AS mois,
    d.month_name AS libelle_mois,
    d.is_ramadan AS periode_ramadan,
    r.region AS region_admin,
    r.country AS zone_geo,
    p.category AS categorie,
    ROUND(SUM(f.total_amount), 2) AS ca_ttc,
    ROUND(SUM(f.total_amount) / 1.20, 2) AS ca_ht,
    COUNT(DISTINCT f.customer_key) AS nb_clients_actifs,
    SUM(f.quantity) AS volume_vendu,
    ROUND(SUM(f.total_amount) / NULLIF(COUNT(DISTINCT f.order_id), 0), 2) AS panier_moyen,
    COUNT(DISTINCT f.order_id) AS nb_commandes
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
JOIN dim_region r ON f.region_key = r.region_key
JOIN dim_product p ON f.product_key = p.product_key
WHERE f.order_status IN ('completed', 'returned')
GROUP BY d.year, d.month, d.month_name, d.is_ramadan, r.region, r.country, p.category;

ALTER TABLE reporting_mv_ca_mensuel
    ADD INDEX idx_rmv_ca_mois (annee, mois),
    ADD INDEX idx_rmv_ca_region (region_admin),
    ADD INDEX idx_rmv_ca_categorie (categorie),
    ADD INDEX idx_rmv_ca_ramadan (periode_ramadan);

-- Vue matérialisée simulée 2 : Top produits par trimestre, avec rang.
DROP TABLE IF EXISTS reporting_mv_top_produits;

CREATE TABLE reporting_mv_top_produits AS
SELECT
    ranked.*,
    RANK() OVER (
        PARTITION BY ranked.annee, ranked.trimestre, ranked.categorie, ranked.ville
        ORDER BY ranked.ca_total DESC
    ) AS rang_dans_categorie
FROM (
    SELECT
        d.year AS annee,
        d.quarter AS trimestre,
        r.city AS ville,
        p.product_name AS nom_produit,
        p.category AS categorie,
        p.brand AS marque,
        SUM(f.quantity) AS qte_totale,
        ROUND(SUM(f.total_amount), 2) AS ca_total,
        COUNT(DISTINCT f.customer_key) AS nb_clients_distincts
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    JOIN dim_product p ON f.product_key = p.product_key
    JOIN dim_region r ON f.region_key = r.region_key
    WHERE f.order_status IN ('completed', 'returned')
    GROUP BY d.year, d.quarter, r.city, p.product_name, p.category, p.brand
) ranked;

ALTER TABLE reporting_mv_top_produits
    ADD INDEX idx_rmv_top_periode (annee, trimestre),
    ADD INDEX idx_rmv_top_ville (ville),
    ADD INDEX idx_rmv_top_categorie (categorie),
    ADD INDEX idx_rmv_top_rang (rang_dans_categorie);

-- Vue matérialisée simulée 3 : Performance des livreurs/transporteurs.
DROP TABLE IF EXISTS reporting_mv_performance_livreurs;

CREATE TABLE reporting_mv_performance_livreurs AS
SELECT
    dd.shipping_company AS nom_livreur,
    dd.delivery_region AS zone_couverture,
    dt.year AS annee,
    dt.month AS mois,
    COUNT(*) AS nb_livraisons,
    ROUND(AVG(f.delivery_delay_days), 2) AS delai_moyen_jours,
    SUM(CASE WHEN dd.delivery_status = 'failed' OR f.delivery_delay_days > 3 THEN 1 ELSE 0 END) AS nb_livraisons_retard,
    ROUND(
        SUM(CASE WHEN dd.delivery_status = 'failed' OR f.delivery_delay_days > 3 THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(*), 0),
        2
    ) AS taux_retard_pct
FROM fact_sales f
JOIN dim_delivery dd ON f.delivery_key = dd.delivery_key
JOIN dim_date dt ON f.date_key = dt.date_key
WHERE f.order_status IN ('completed', 'returned')
  AND f.delivery_delay_days IS NOT NULL
GROUP BY dd.shipping_company, dd.delivery_region, dt.year, dt.month;

ALTER TABLE reporting_mv_performance_livreurs
    ADD INDEX idx_rmv_livreur_periode (annee, mois),
    ADD INDEX idx_rmv_livreur_nom (nom_livreur),
    ADD INDEX idx_rmv_livreur_zone (zone_couverture);

-- Requêtes de contrôle rapides.
SELECT 'dim_livreur' AS objet, COUNT(*) AS lignes FROM dim_livreur
UNION ALL SELECT 'reporting_mv_ca_mensuel', COUNT(*) FROM reporting_mv_ca_mensuel
UNION ALL SELECT 'reporting_mv_top_produits', COUNT(*) FROM reporting_mv_top_produits
UNION ALL SELECT 'reporting_mv_performance_livreurs', COUNT(*) FROM reporting_mv_performance_livreurs;
