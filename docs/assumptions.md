# Hypothèses du projet

1. Mexora est une entreprise fictive basée à Tanger.
2. Les données sont générées artificiellement pour un usage académique.
3. Le système transactionnel est représenté par MySQL `mexora_oltp`.
4. Le Data Warehouse est représenté par MySQL `mexora_dw`.
5. Le dashboard final officiel est conçu avec Metabase, conformément à l'option acceptée dans le cahier de charge.
6. Streamlit reste un prototype complémentaire Python, non prioritaire dans le rendu final.
7. Power BI est uniquement une amélioration future possible sous Windows.
8. L'environnement local validé utilise une instance MySQL projet isolée sur `127.0.0.1:3307` lorsque le compte `root` système n'est pas accessible.
9. Ramadan 2026 est approximé du 18 février 2026 au 19 mars 2026.
10. Une commande peut contenir plusieurs produits.
11. Les retours peuvent concerner une commande ou un produit précis.
12. Les anomalies sont corrigées, supprimées ou isolées selon les règles de qualité.
13. Le chiffre d'affaires est calculé après remise mais avant remboursement, sauf indication contraire.
14. Les valeurs manquantes sont traitées selon les règles définies dans l'ETL.
15. Le schéma en étoile est choisi pour optimiser l'analyse décisionnelle.
16. Le cahier recommande PostgreSQL ; MySQL est conservé dans ce rendu pour garder une architecture cohérente de bout en bout avec la source transactionnelle et l'environnement local validé.
17. Les scripts `sql/postgres/` sont fournis comme référence académique stricte, mais la validation opérationnelle se fait sur MySQL isolé.
18. Les fichiers `data/academic_raw/*` reproduisent les structures brutes demandées par le cahier de charge ; le pipeline validé exploite ensuite l'OLTP MySQL et la zone `data/raw/`.
19. La dimension `dim_livreur` est représentée par les transporteurs, faute d'identifiant livreur individuel dans l'ETL validé.
20. Les documents `modeling_justification.pdf` et `insights_metier.pdf` sont générés à partir des documents Markdown correspondants.
17. MySQL ne fournit pas de vues matérialisées natives ; elles sont simulées par des tables de reporting rafraîchissables dans `sql/06_reporting_views_mysql.sql`.
18. La dimension livreur est représentée par le transporteur (`shipping_company`) parce que les données générées ne contiennent pas d'identifiant livreur individuel.
