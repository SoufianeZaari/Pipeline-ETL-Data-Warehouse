# Dashboard BI final

Le dashboard final officiel du projet Mexora est réalisé avec Metabase. Il se connecte au Data Warehouse MySQL `mexora_dw` et peut être généré automatiquement via l'API Metabase avec :

```bash
python metabase/create_mexora_dashboard.py
```

Streamlit reste disponible dans `dashboard/streamlit_app.py` comme prototype complémentaire Python, utile pour explorer les données localement.

## Dashboard Metabase

Nom du dashboard :

```text
Mexora BI Dashboard
```

Source :

```text
MySQL 127.0.0.1:3307 / mexora_dw
```

Collection :

```text
Mexora BI Project
```

## Questions métier obligatoires couvertes

| Question du cahier de charge | Réponse dans le dashboard |
|---|---|
| Quelle région génère le plus de CA et quelle est l'évolution mensuelle ? | `Cahier - Evolution CA mensuelle par région` |
| Quels sont les 10 produits les plus vendus par trimestre à Tanger ? | `Cahier - Top produits trimestriels à Tanger` |
| Quel segment client a le panier moyen le plus élevé ? | `Cahier - Panier moyen par segment client` |
| Quel est le taux de retour par catégorie ? | `Cahier - Taux retour catégorie avec alerte` |
| Y a-t-il un effet Ramadan sur l'alimentation ? | `Cahier - Effet Ramadan alimentation` |

## KPIs disponibles

- chiffre d'affaires total ;
- nombre de commandes ;
- panier moyen ;
- taux de retour global ;
- délai moyen de livraison ;
- montant remboursé total.

## Analyses disponibles

- chiffre d'affaires par mois ;
- chiffre d'affaires par région ;
- chiffre d'affaires par catégorie ;
- chiffre d'affaires par ville ;
- top 10 clients ;
- top clients à Tanger ;
- clients par région ;
- panier moyen par région ;
- top produits vendus ;
- produits les plus retournés ;
- performance Ramadan ;
- taux de retour par région ;
- délai moyen par région ;
- statuts de livraison ;
- répartition des paiements ;
- anomalies par type ;
- résumé qualité des données.

## Lancement

```bash
cd "/home/soufiane/DATAEng/Miniprojet 1/mexora-bi-project"
source .venv/bin/activate
python scripts/start_project_mysql.py
python scripts/run_etl.py --regenerate
bash metabase/start_metabase.sh
python metabase/create_mexora_dashboard.py
```

Ouvrir ensuite l'URL affichée par le script, par exemple :

```text
http://localhost:3000/dashboard/2
```
