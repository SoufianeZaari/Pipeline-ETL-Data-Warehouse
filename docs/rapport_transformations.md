# Rapport des transformations

Ce rapport documente les principales règles appliquées par `scripts/transform.py`. Les volumes sont issus de la dernière exécution validée du pipeline.

Le cahier de charge demande également des fichiers bruts sous les noms `commandes_mexora.csv`, `produits_mexora.json`, `clients_mexora.csv` et `regions_maroc.csv`. Ils sont générés par `scripts/generate_academic_assets.py` dans `data/academic_raw/`. Le pipeline opérationnel validé conserve toutefois son flux MySQL OLTP -> raw CSV -> Pandas -> MySQL DW.

## Fichiers bruts académiques

| Fichier | Nombre de lignes | Problèmes intentionnels présents | Statut |
|---|---:|---|---|
| `data/academic_raw/commandes_mexora.csv` | 50000 | doublons `id_commande`, dates mixtes, villes incohérentes, statuts hétérogènes, quantités/prix invalides, livreurs manquants | conforme |
| `data/academic_raw/produits_mexora.json` | 300 | catégories hétérogènes, prix catalogue manquants, produits inactifs | conforme |
| `data/academic_raw/clients_mexora.csv` | 1000 | emails invalides/dupliqués, sexes hétérogènes, âges à valider, villes non standardisées | conforme |
| `data/academic_raw/regions_maroc.csv` | 12 | référentiel volontairement utilisé pour harmoniser les villes et régions | conforme |

## Synthèse des volumes

| Objet | Lignes |
|---|---:|
| customers extraits | 1000 |
| products extraits | 300 |
| orders extraits | 5000 |
| order_items extraits | 9424 |
| payments extraits | 5000 |
| deliveries extraits | 5000 |
| returns extraits | 738 |
| fact_sales produites | 9061 |
| anomalies détectées | 1559 |
| anomalies corrigées | 1196 |
| anomalies supprimées | 363 |

## Règles clients

| Règle | Traitement appliqué | Impact |
|---|---|---:|
| Identifiant client invalide ou dupliqué | suppression de la ligne | compté dans `quality_issues` |
| Email invalide | remplacement par `unknown_email_{customer_id}@mexora.local` | corrigé |
| Email dupliqué | remplacement par `duplicate_email_{customer_id}@mexora.local` | corrigé |
| Ville incohérente | standardisation (`TNG`, `Tnja`, `Tangier` -> `Tanger`) | corrigé |
| Région incohérente | standardisation à partir de la ville si possible | corrigé |
| Date d'inscription invalide | remplacement par `2025-01-01` | corrigé |
| Sexe hétérogène | normalisation en `Male`, `Female` ou `Unknown` | corrigé |
| Segment client | calcul `Gold/Silver/Bronze` depuis le CA client | enrichissement |

## Règles produits

| Règle | Traitement appliqué | Impact |
|---|---|---:|
| Produit invalide ou dupliqué | suppression de la ligne | supprimé |
| Prix catalogue nul, négatif ou aberrant | correction par médiane de catégorie, sinon `100.0` | corrigé |
| Catégorie/sous-catégorie manquante | remplacement par `Unknown` si nécessaire | corrigé |
| Date de création invalide | remplacement par `2025-01-01` | corrigé |
| Produit inactif | conservation de l'attribut `actif` pour l'analyse et préparation SCD | documenté |
| Historisation produit | ajout conceptuel `date_debut`, `date_fin`, `est_actif` dans la façade académique | SCD-ready |

## Règles commandes

| Règle | Traitement appliqué | Impact |
|---|---|---:|
| Commande dupliquée | suppression, conservation d'une seule occurrence valide | supprimé |
| Client inconnu | suppression de la commande | supprimé |
| Date de commande invalide | suppression de la commande | supprimé |
| Statut non standard | mapping vers `completed`, `cancelled`, `pending`, `returned`, `failed` ou `unknown` | corrigé |

## Règles lignes de commande

| Règle | Traitement appliqué | Impact |
|---|---|---:|
| Ligne dupliquée | suppression | supprimé |
| Commande ou produit inexistant | suppression | supprimé |
| Quantité `<= 0` | suppression | supprimé |
| Prix unitaire `<= 0` ou aberrant | suppression et isolation dans `quality_issues` | supprimé |
| Remise invalide | remise remplacée par `0` | corrigé |

## Règles paiements

| Règle | Traitement appliqué | Impact |
|---|---|---:|
| Paiement sans commande | suppression | supprimé |
| Plusieurs paiements pour une même commande | conservation d'un paiement, suppression des doublons | supprimé |
| Statut de paiement ambigu | remplacement par `unknown` | corrigé |
| Montant payé négatif | remplacement par `0` | corrigé |

## Règles livraisons

| Règle | Traitement appliqué | Impact |
|---|---|---:|
| Livraison sans commande | suppression | supprimé |
| Livraison dupliquée pour une commande | conservation d'une livraison | supprimé |
| Date d'expédition manquante | estimation à `order_date + 1 jour` | corrigé |
| Date d'expédition avant commande | correction à `order_date + 1 jour` | corrigé |
| Date de livraison manquante pour livraison livrée | estimation à `shipped_date + 3 jours` | corrigé |
| Date de livraison avant commande | correction automatique | corrigé |
| Ville/région de livraison incohérentes | standardisation géographique | corrigé |

## Règles retours

| Règle | Traitement appliqué | Impact |
|---|---|---:|
| Retour dupliqué | suppression | supprimé |
| Retour sans commande ou produit valide | suppression | supprimé |
| Montant remboursé négatif | remplacement par `0` | corrigé |

## Construction décisionnelle

| Objet | Règle de construction |
|---|---|
| `dim_date` | génération complète entre la première et la dernière date de commande |
| `is_ramadan` | vrai du 18 février 2026 au 19 mars 2026 |
| `dim_region` | union des régions clients et régions de livraison |
| `dim_payment` | combinaisons méthode/statut de paiement |
| `dim_delivery` | combinaisons statut/transporteur/ville/région |
| `fact_sales` | une ligne par ligne de commande valide |
| `total_amount` | `quantity * unit_price * (1 - discount_rate)` |
| `amount_paid` | montant payé réparti au prorata du total de la commande |
| `is_returned` | indicateur binaire basé sur la table des retours |
| `delivery_delay_days` | différence entre date de livraison et date de commande |

## Résultat qualité final

Les contrôles confirment que le Data Warehouse ne contient :

- aucun montant négatif dans `fact_sales` ;
- aucune quantité invalide dans `fact_sales` ;
- aucun fait sans dimension correspondante.

## Correspondance avec les règles obligatoires du cahier

| Règle du cahier | Implémentation dans le projet |
|---|---|
| Doublons commandes | `clean_orders()` supprime les commandes dupliquées ; `clean_commandes.py` conserve la dernière occurrence dans la façade académique |
| Dates en formats mixtes | `parse_date()` et `pd.to_datetime(..., format="mixed")` standardisent les dates |
| Villes incohérentes | `standardize_city()` et le référentiel `regions_maroc.csv` harmonisent les villes |
| Statuts `OK`, `KO`, `DONE` | mapping vers statuts décisionnels normalisés |
| Quantités négatives ou nulles | lignes supprimées avant `fact_sales` |
| Prix à 0 ou aberrants | commandes test supprimées ou prix catalogue corrigé selon le contexte |
| Livreurs manquants | représentés par `Unknown`/`-1` ou par transporteur selon le flux |
| Segmentation Gold/Silver/Bronze | calculée depuis le chiffre d'affaires client |
| SCD | SCD Type 1 appliqué aux corrections ; SCD Type 2 préparé par `date_debut`, `date_fin`, `est_actif` |
