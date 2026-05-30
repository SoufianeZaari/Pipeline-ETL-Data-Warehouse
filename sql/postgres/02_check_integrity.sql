-- ============================================================
-- Mexora Analytics - Contrôles d'intégrité PostgreSQL
-- ============================================================

SELECT 'dim_temps' AS objet, COUNT(*) AS lignes FROM dwh_mexora.dim_temps
UNION ALL SELECT 'dim_produit', COUNT(*) FROM dwh_mexora.dim_produit
UNION ALL SELECT 'dim_client', COUNT(*) FROM dwh_mexora.dim_client
UNION ALL SELECT 'dim_region', COUNT(*) FROM dwh_mexora.dim_region
UNION ALL SELECT 'dim_livreur', COUNT(*) FROM dwh_mexora.dim_livreur
UNION ALL SELECT 'fait_ventes', COUNT(*) FROM dwh_mexora.fait_ventes;

SELECT 'faits_sans_date' AS controle, COUNT(*) AS anomalies
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_temps d ON f.id_date = d.id_date
WHERE d.id_date IS NULL
UNION ALL
SELECT 'faits_sans_produit', COUNT(*)
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_produit p ON f.id_produit = p.id_produit_sk
WHERE p.id_produit_sk IS NULL
UNION ALL
SELECT 'faits_sans_client', COUNT(*)
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_client c ON f.id_client = c.id_client_sk
WHERE c.id_client_sk IS NULL
UNION ALL
SELECT 'faits_sans_region', COUNT(*)
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_region r ON f.id_region = r.id_region
WHERE r.id_region IS NULL
UNION ALL
SELECT 'quantites_invalides', COUNT(*)
FROM dwh_mexora.fait_ventes
WHERE quantite_vendue <= 0
UNION ALL
SELECT 'montants_negatifs', COUNT(*)
FROM dwh_mexora.fait_ventes
WHERE montant_ttc < 0 OR montant_ht < 0;

