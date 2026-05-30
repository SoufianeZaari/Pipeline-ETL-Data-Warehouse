-- ============================================================
-- Mexora Analytics - DWH PostgreSQL de référence académique
-- Schémas: staging_mexora, dwh_mexora, reporting_mexora
-- ============================================================
--
-- Le projet exécutable fourni utilise MySQL isolé, car l'environnement local
-- validé du mini-projet repose sur MySQL. Ce script PostgreSQL documente une
-- implémentation stricte conforme à l'énoncé, prête à être utilisée si le
-- moteur PostgreSQL est exigé.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS staging_mexora;
CREATE SCHEMA IF NOT EXISTS dwh_mexora;
CREATE SCHEMA IF NOT EXISTS reporting_mexora;

DROP TABLE IF EXISTS dwh_mexora.fait_ventes CASCADE;
DROP TABLE IF EXISTS dwh_mexora.dim_livreur CASCADE;
DROP TABLE IF EXISTS dwh_mexora.dim_region CASCADE;
DROP TABLE IF EXISTS dwh_mexora.dim_client CASCADE;
DROP TABLE IF EXISTS dwh_mexora.dim_produit CASCADE;
DROP TABLE IF EXISTS dwh_mexora.dim_temps CASCADE;

CREATE TABLE dwh_mexora.dim_temps (
    id_date INTEGER PRIMARY KEY,
    date_complete DATE NOT NULL UNIQUE,
    jour SMALLINT NOT NULL CHECK (jour BETWEEN 1 AND 31),
    mois SMALLINT NOT NULL CHECK (mois BETWEEN 1 AND 12),
    trimestre SMALLINT NOT NULL CHECK (trimestre BETWEEN 1 AND 4),
    annee SMALLINT NOT NULL,
    semaine SMALLINT,
    libelle_jour VARCHAR(20),
    libelle_mois VARCHAR(20),
    est_weekend BOOLEAN DEFAULT FALSE,
    est_ferie_maroc BOOLEAN DEFAULT FALSE,
    periode_ramadan BOOLEAN DEFAULT FALSE
);

CREATE TABLE dwh_mexora.dim_produit (
    id_produit_sk SERIAL PRIMARY KEY,
    id_produit_nk VARCHAR(20) NOT NULL,
    nom_produit VARCHAR(200) NOT NULL,
    categorie VARCHAR(100),
    sous_categorie VARCHAR(100),
    marque VARCHAR(100),
    fournisseur VARCHAR(100),
    prix_standard DECIMAL(10,2),
    origine_pays VARCHAR(50),
    date_debut DATE NOT NULL DEFAULT CURRENT_DATE,
    date_fin DATE NOT NULL DEFAULT '9999-12-31',
    est_actif BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_dim_produit_version UNIQUE (id_produit_nk, date_debut)
);

CREATE TABLE dwh_mexora.dim_client (
    id_client_sk SERIAL PRIMARY KEY,
    id_client_nk VARCHAR(20) NOT NULL,
    nom_complet VARCHAR(200),
    tranche_age VARCHAR(10),
    sexe CHAR(1),
    ville VARCHAR(100),
    region_admin VARCHAR(100),
    segment_client VARCHAR(20) CHECK (segment_client IN ('Gold', 'Silver', 'Bronze')),
    canal_acquisition VARCHAR(50),
    date_debut DATE NOT NULL DEFAULT CURRENT_DATE,
    date_fin DATE NOT NULL DEFAULT '9999-12-31',
    est_actif BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_dim_client_version UNIQUE (id_client_nk, date_debut)
);

CREATE TABLE dwh_mexora.dim_region (
    id_region SERIAL PRIMARY KEY,
    ville VARCHAR(100) NOT NULL,
    province VARCHAR(100),
    region_admin VARCHAR(100),
    zone_geo VARCHAR(50),
    pays VARCHAR(50) DEFAULT 'Maroc',
    CONSTRAINT uq_dim_region_ville UNIQUE (ville, region_admin)
);

CREATE TABLE dwh_mexora.dim_livreur (
    id_livreur SERIAL PRIMARY KEY,
    id_livreur_nk VARCHAR(20),
    nom_livreur VARCHAR(100),
    type_transport VARCHAR(50),
    zone_couverture VARCHAR(100)
);

CREATE TABLE dwh_mexora.fait_ventes (
    id_vente BIGSERIAL PRIMARY KEY,
    id_commande VARCHAR(30) NOT NULL,
    id_date INTEGER NOT NULL REFERENCES dwh_mexora.dim_temps(id_date),
    id_produit INTEGER NOT NULL REFERENCES dwh_mexora.dim_produit(id_produit_sk),
    id_client INTEGER NOT NULL REFERENCES dwh_mexora.dim_client(id_client_sk),
    id_region INTEGER NOT NULL REFERENCES dwh_mexora.dim_region(id_region),
    id_livreur INTEGER REFERENCES dwh_mexora.dim_livreur(id_livreur),
    quantite_vendue INTEGER NOT NULL CHECK (quantite_vendue > 0),
    montant_ht DECIMAL(12,2) NOT NULL CHECK (montant_ht >= 0),
    montant_ttc DECIMAL(12,2) NOT NULL CHECK (montant_ttc >= 0),
    cout_livraison DECIMAL(8,2),
    delai_livraison_jours SMALLINT,
    remise_pct DECIMAL(5,2) DEFAULT 0,
    date_chargement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    statut_commande VARCHAR(20) CHECK (statut_commande IN ('livré','annulé','en_cours','retourné'))
);

CREATE INDEX idx_fv_date ON dwh_mexora.fait_ventes(id_date);
CREATE INDEX idx_fv_produit ON dwh_mexora.fait_ventes(id_produit);
CREATE INDEX idx_fv_client ON dwh_mexora.fait_ventes(id_client);
CREATE INDEX idx_fv_region ON dwh_mexora.fait_ventes(id_region);
CREATE INDEX idx_fv_livreur ON dwh_mexora.fait_ventes(id_livreur);
CREATE INDEX idx_fv_date_region ON dwh_mexora.fait_ventes(id_date, id_region) INCLUDE (montant_ttc, quantite_vendue);
CREATE INDEX idx_fv_statut_livre ON dwh_mexora.fait_ventes(statut_commande) WHERE statut_commande = 'livré';

