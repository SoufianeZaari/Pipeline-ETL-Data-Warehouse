# Metabase BI Dashboard

Metabase est utilisé comme outil BI pour explorer le Data Warehouse MySQL `mexora_dw`.

## Pourquoi utiliser `$HOME/DATAEng/mexora_metabase`

Le chemin original du projet contient un espace :

```text
/home/soufiane/DATAEng/Miniprojet 1/mexora-bi-project/metabase/metabase.jar
```

Java peut échouer avec :

```text
java.net.URISyntaxException: Illegal character in opaque part
```

Pour éviter ce problème, `metabase/start_metabase.sh` copie automatiquement `metabase.jar` vers un dossier sans espace :

```text
$HOME/DATAEng/mexora_metabase/metabase.jar
```

Metabase est ensuite lancé depuis ce dossier, et les logs sont écrits dans :

```text
$HOME/DATAEng/mexora_metabase/metabase.log
```

## Démarrer MySQL projet et l'ETL

```bash
cd "/home/soufiane/DATAEng/Miniprojet 1/mexora-bi-project"
source .venv/bin/activate
python scripts/start_project_mysql.py
python scripts/run_etl.py --regenerate
```

## Démarrer Metabase

```bash
cd "/home/soufiane/DATAEng/Miniprojet 1/mexora-bi-project"
bash metabase/start_metabase.sh
```

Ouvrir ensuite :

```text
http://localhost:3000
```

## Connexion Metabase à MySQL

Dans l'assistant Metabase, choisir :

| Champ | Valeur |
|---|---|
| Type | MySQL |
| Host | `127.0.0.1` |
| Port | `3307` |
| Database | `mexora_dw` |
| Username | `mexora_user` |
| Password | `mexora_pass` |

## Vérifier le port

```bash
ss -ltnp | grep 3000
```

## Automatiser la création du dashboard

Le dashboard `Mexora BI Dashboard` peut être créé automatiquement via l'API Metabase. Le script crée une collection `Mexora BI Project`, ajoute les questions SQL, puis les place dans un dashboard organisé.

Créer d'abord un fichier d'identifiants local non versionné :

```bash
cd "/home/soufiane/DATAEng/Miniprojet 1/mexora-bi-project"
cp metabase/.metabase_env.example metabase/.metabase_env
```

Modifier ensuite `metabase/.metabase_env` :

```text
METABASE_URL=http://localhost:3000
METABASE_EMAIL=MON_EMAIL_METABASE
METABASE_PASSWORD=MON_PASSWORD_METABASE
METABASE_DATABASE_NAME=Mexora Data Warehouse
```

`METABASE_DATABASE_NAME=mexora_dw` est aussi accepté par le script : il est résolu automatiquement vers la connexion Metabase `Mexora Data Warehouse`.

Lancer l'automatisation :

```bash
source .venv/bin/activate
python metabase/create_mexora_dashboard.py
```

Le script affiche l'URL du dashboard, le nombre de questions créées, le nombre de questions mises à jour et les erreurs éventuelles avec l'endpoint Metabase concerné.

Si l'API répond `Connections could not be acquired from the underlying database`, Metabase écoute bien sur le port 3000 mais son stockage interne n'est pas encore disponible. Relancer `bash metabase/start_metabase.sh`, attendre quelques secondes, puis relancer `python metabase/create_mexora_dashboard.py`.

Si l'API crée les questions mais échoue sur `REPORT_DASHBOARDCARD` ou `PRIMARY KEY`, le problème vient du stockage interne Metabase utilisé pour les positions des cartes. Les questions SQL restent utilisables ; il suffit alors d'ajouter manuellement les cartes déjà créées dans `Mexora BI Dashboard`.

Méthode manuelle si l'API reste instable :

1. ouvrir `http://localhost:3000` ;
2. choisir `New > SQL Query` ;
3. coller les requêtes depuis `metabase/questions_sql.md` ;
4. sauvegarder chaque question dans `Mexora BI Project` ;
5. utiliser `Add to dashboard > Mexora BI Dashboard` ;
6. répéter au minimum pour les cinq questions obligatoires ;
7. prendre les captures pour le rapport.

Le dashboard inclut aussi les cinq questions obligatoires du cahier de charge :

- évolution du chiffre d'affaires mensuel par région ;
- top produits trimestriels à Tanger ;
- panier moyen par segment client ;
- taux de retour par catégorie avec seuil d'alerte ;
- effet Ramadan sur l'alimentation.

Les requêtes utilisées sont documentées dans :

```text
metabase/questions_sql.md
```

Le plan d'organisation du dashboard est documenté dans :

```text
metabase/dashboard_plan.md
```

Après création, ouvrir le dashboard affiché par le script et prendre les captures nécessaires pour le rapport.

## Java

Si Java n'est pas installé :

```bash
sudo apt install openjdk-21-jre -y
```

Le script vérifie automatiquement `java -version` avant de lancer Metabase.
