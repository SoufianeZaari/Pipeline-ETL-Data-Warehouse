# Plan du dashboard Metabase - Mexora BI Dashboard

## Structure

Le dashboard `Mexora BI Dashboard` est organisé en sept blocs :

1. KPIs globaux en haut.
2. Ventes par mois, région, catégorie et ville.
3. Analyse clients.
4. Analyse produits.
5. Livraisons et retours.
6. Qualité des données.
7. Questions obligatoires du cahier de charge.

## Grille Metabase

- Colonnes Metabase : 24.
- KPIs : 6 cards en ligne, largeur 4.
- Graphiques principaux : largeur 12.
- Tableaux détaillés : largeur 12 ou 24 selon lisibilité.

## Questions obligatoires

- Evolution CA mensuelle par région.
- Top produits trimestriels à Tanger.
- Panier moyen par segment client.
- Taux retour catégorie avec alerte.
- Effet Ramadan alimentation.

## Source

Toutes les questions utilisent des requêtes SQL natives sur la base Metabase :

```text
Mexora Data Warehouse
```

Cette base pointe vers MySQL `mexora_dw` sur `127.0.0.1:3307`.
