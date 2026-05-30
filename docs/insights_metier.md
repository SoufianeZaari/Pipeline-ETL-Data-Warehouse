# Insights métier Mexora

Ce document synthétise les principaux enseignements attendus du dashboard Metabase `Mexora BI Dashboard`.

## 1. Régions et villes génératrices de chiffre d'affaires

Le Data Warehouse contient `9061` lignes de fait exploitables. Le chiffre d'affaires total validé atteint `45 585 294,79`, avec un panier moyen de `9272,84` par commande. Les villes les plus contributrices sont Tanger (`7 929 134,03`), Casablanca (`7 793 512,26`) et Rabat (`6 035 813,69`).

Cette lecture confirme que Tanger reste un marché prioritaire pour Mexora, mais que Casablanca est très proche en valeur. La direction peut donc arbitrer entre consolidation du marché local tangérois et accélération commerciale dans les grandes métropoles.

## 2. Catégories les plus rentables

La catégorie `Electronics` domine nettement le chiffre d'affaires avec `37 619 680,75`, devant `Fashion` avec `6 753 550,38` et `Food` avec `1 212 063,66`. Ce résultat est cohérent avec une marketplace e-commerce où les produits électroniques ont un prix unitaire plus élevé.

Mexora doit donc sécuriser les stocks et les fournisseurs électroniques, tout en utilisant les catégories Fashion et Food comme leviers de fréquence d'achat et de saisonnalité.

## 3. Segments clients

La segmentation `Gold/Silver/Bronze` permet de distinguer les clients à forte valeur des clients plus occasionnels. Le panier moyen par segment aide à adapter les offres de fidélisation et les avantages commerciaux.

## 4. Retours produits

Le taux de retour global validé est de `7,87 %`. Par catégorie, les taux sont proches : `Food` à `7,98 %`, `Fashion` à `7,93 %` et `Electronics` à `7,68 %`. Comme chaque catégorie dépasse le seuil d'alerte de 5 %, la priorité n'est pas seulement produit : il faut aussi analyser les descriptions, la préparation de commande, la promesse de livraison et la politique de remboursement.

## 5. Effet Ramadan

L'indicateur Ramadan dans `dim_date` compare les ventes d'alimentation pendant et hors Ramadan. Sur les données générées, le chiffre d'affaires Food pendant Ramadan est de `50 054,42` pour un volume de `357`, contre `927 313,44` et `7830` hors Ramadan. L'indice de performance journalier ressort à `91,20` base 100 hors Ramadan.

L'analyse doit être lue avec prudence : la période Ramadan 2026 est approximée du 18 février 2026 au 19 mars 2026 et les données sont artificielles. Elle démontre néanmoins comment une période métier spécifique peut être intégrée dans une dimension temps et utilisée pour ajuster les stocks alimentaires.

## 6. Livraison

Le délai moyen de livraison validé est de `14,99` jours. Ce niveau est élevé pour une marketplace e-commerce et doit être suivi par région et par transporteur dans Metabase. Une recommandation prioritaire consiste à identifier les régions lentes, négocier les SLA transporteurs et suivre mensuellement le taux d'échec de livraison.

## Conclusion

Le Data Warehouse transforme les données opérationnelles de Mexora en indicateurs exploitables. Les recommandations principales sont de protéger la performance Electronics, renforcer Tanger et Casablanca, réduire le taux de retour au-dessous de 5 %, et piloter les transporteurs avec un objectif de réduction du délai moyen de livraison.
