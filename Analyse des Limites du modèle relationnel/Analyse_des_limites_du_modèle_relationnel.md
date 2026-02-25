# Phase 2 : Analyse des limites du modèle relationnel et proposition du modèle Graphe
## 1. Analyse des limites du modèle relationnel

Bien que le modèle relationnel (SQL) mis en place lors de la Phase 1 garantisse l'intégrité et l'absence de redondance des données, il présente des limites majeures pour l'analyse avancée des statistiques criminelles :

* Problème de performances (Les jointures lourdes) : Notre table centrale Fait_Statistique contient des millions de lignes. Pour savoir quels départements ont le plus de cambriolages, le moteur SQL doit faire une jointure (JOIN) entre les tables Departement, Service, Fait_Statistique et Infraction. Plus le volume de données augmente, plus ces opérations mathématiques (produits cartésiens filtrés) consomment du CPU et de la RAM, dégradant les temps de réponse.

* Problème de lisibilité des requêtes : Pour répondre à des questions métiers analytiques ("Quels sont les types de crimes communs entre deux départements voisins gérés par la Gendarmerie ?"), la syntaxe SQL devient extrêmement verbeuse, imbriquant des sous-requêtes et de multiples jointures, ce qui rend le code difficile à maintenir.

* Incapacité à traiter les relations complexes et les réseaux : Le cahier des charges demande l'ajout d'adjacences (départements/communes frontaliers). Le SQL n'est pas fait pour calculer des "chemins" ou naviguer dans un réseau (ex: trouver l'influence d'un type de crime de proche en proche). Le relationnel relie des clés, pas des concepts.

## 2. Proposition d'un modèle orienté Graphe (Neo4j)

Pour pallier ces limites, nous proposons la migration vers une base de données orientée Graphe. Dans ce modèle, la relation entre deux données est stockée physiquement au même titre que la donnée elle-même (Index-Free Adjacency), rendant la navigation quasi-instantanée.

### A. Définition des Nœuds (Nodes / Entités) :
Nous allons transformer nos tables en labels de nœuds.

    (:Departement {code_dept: "01"}) : Représente une zone géographique. (Nous pourrons l'enrichir plus tard avec des nœuds Région ou Commune).

    (:Service {id_service: 1, nom: "CSP BOURG EN BRESSE", perimetre: "DCSP", force: "PN"}) : Représente une unité des forces de l'ordre.

    (:Infraction {code_index: 4, libelle: "Vols à main armée"}) : Représente le type de crime/délit.

### B. Définition des Relations (Edges) :
C'est ici que la table de faits disparaît au profit de relations riches portant des propriétés.

    (:Service)-[:SITUE_DANS]->(:Departement) : Lie l'unité à sa géographie.

    (:Service)-[:A_ENREGISTRE {annee: 2021, nombre_faits: 15}]->(:Infraction) : C'est la transformation clé. La table Fait_Statistique devient une flèche qui relie directement le commissariat au délit. L'année et le volume deviennent des propriétés (attributs) de cette flèche.

    (:Departement)-[:EST_VOISIN_DE]->(:Departement) : (Anticipation de l'enrichissement demandé dans le cahier des charges) pour analyser la propagation géographique de la délinquance.