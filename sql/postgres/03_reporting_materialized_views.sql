-- ============================================================
-- Mexora Analytics - Vues matérialisées PostgreSQL
-- ============================================================

DROP MATERIALIZED VIEW IF EXISTS reporting_mexora.mv_performance_livreurs;
DROP MATERIALIZED VIEW IF EXISTS reporting_mexora.mv_top_produits;
DROP MATERIALIZED VIEW IF EXISTS reporting_mexora.mv_ca_mensuel;

CREATE MATERIALIZED VIEW reporting_mexora.mv_ca_mensuel AS
SELECT
    t.annee,
    t.mois,
    t.libelle_mois,
    t.periode_ramadan,
    r.region_admin,
    r.zone_geo,
    p.categorie,
    SUM(f.montant_ttc) AS ca_ttc,
    SUM(f.montant_ht) AS ca_ht,
    COUNT(DISTINCT f.id_client) AS nb_clients_actifs,
    SUM(f.quantite_vendue) AS volume_vendu,
    ROUND(SUM(f.montant_ttc) / NULLIF(COUNT(DISTINCT f.id_commande), 0), 2) AS panier_moyen,
    COUNT(DISTINCT f.id_commande) AS nb_commandes
FROM dwh_mexora.fait_ventes f
JOIN dwh_mexora.dim_temps t ON f.id_date = t.id_date
JOIN dwh_mexora.dim_region r ON f.id_region = r.id_region
JOIN dwh_mexora.dim_produit p ON f.id_produit = p.id_produit_sk
WHERE f.statut_commande = 'livré'
GROUP BY t.annee, t.mois, t.libelle_mois, t.periode_ramadan, r.region_admin, r.zone_geo, p.categorie
WITH DATA;

CREATE INDEX idx_mv_ca_mensuel_periode ON reporting_mexora.mv_ca_mensuel(annee, mois);
CREATE INDEX idx_mv_ca_mensuel_region ON reporting_mexora.mv_ca_mensuel(region_admin);
CREATE INDEX idx_mv_ca_mensuel_categorie ON reporting_mexora.mv_ca_mensuel(categorie);

CREATE MATERIALIZED VIEW reporting_mexora.mv_top_produits AS
SELECT
    t.annee,
    t.trimestre,
    p.nom_produit,
    p.categorie,
    p.marque,
    SUM(f.quantite_vendue) AS qte_totale,
    SUM(f.montant_ttc) AS ca_total,
    COUNT(DISTINCT f.id_client) AS nb_clients_distincts,
    RANK() OVER (
        PARTITION BY t.annee, t.trimestre, p.categorie
        ORDER BY SUM(f.montant_ttc) DESC
    ) AS rang_dans_categorie
FROM dwh_mexora.fait_ventes f
JOIN dwh_mexora.dim_temps t ON f.id_date = t.id_date
JOIN dwh_mexora.dim_produit p ON f.id_produit = p.id_produit_sk
WHERE f.statut_commande = 'livré'
GROUP BY t.annee, t.trimestre, p.nom_produit, p.categorie, p.marque
WITH DATA;

CREATE INDEX idx_mv_top_produits_periode ON reporting_mexora.mv_top_produits(annee, trimestre);
CREATE INDEX idx_mv_top_produits_categorie ON reporting_mexora.mv_top_produits(categorie);

CREATE MATERIALIZED VIEW reporting_mexora.mv_performance_livreurs AS
SELECT
    l.nom_livreur,
    l.zone_couverture,
    t.annee,
    t.mois,
    COUNT(*) AS nb_livraisons,
    AVG(f.delai_livraison_jours) AS delai_moyen_jours,
    COUNT(*) FILTER (WHERE f.delai_livraison_jours > 3) AS nb_livraisons_retard,
    ROUND(COUNT(*) FILTER (WHERE f.delai_livraison_jours > 3) * 100.0 / NULLIF(COUNT(*), 0), 2) AS taux_retard_pct
FROM dwh_mexora.fait_ventes f
JOIN dwh_mexora.dim_livreur l ON f.id_livreur = l.id_livreur
JOIN dwh_mexora.dim_temps t ON f.id_date = t.id_date
WHERE f.statut_commande IN ('livré', 'retourné')
  AND f.delai_livraison_jours IS NOT NULL
GROUP BY l.nom_livreur, l.zone_couverture, t.annee, t.mois
WITH DATA;

CREATE INDEX idx_mv_livreurs_periode ON reporting_mexora.mv_performance_livreurs(annee, mois);
CREATE INDEX idx_mv_livreurs_nom ON reporting_mexora.mv_performance_livreurs(nom_livreur);

