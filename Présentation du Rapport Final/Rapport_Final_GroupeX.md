# 1. Les différentes méthodes de migration (SQL vers Graphe)

Dans le cadre d'une migration d'un modèle relationnel vers un modèle graphe, plusieurs approches existent. Le choix dépend du volume de données, de la fréquence de mise à jour (migration "One-shot" vs synchronisation continue) et des compétences techniques de l'équipe :

* Méthode 1 : L'approche ETL (Extract, Transform, Load) par script sur mesure (Celle que nous avons choisie)
    * Principe : Utilisation d'un langage de programmation (ex: Python avec Pandas et le driver officiel Neo4j) pour extraire les données, les nettoyer en mémoire, purger les types incompatibles, puis les injecter par "lots" (batching) via des requêtes Cypher (UNWIND).

    * Avantage : Contrôle total sur la transformation (comme la conversion d'une table de faits en relations). Idéal pour des nettoyages complexes.

* Méthode 2 : L'utilisation de plugins d'intégration directe (ex: Neo4j APOC)
    * Principe : La librairie APOC (Awesome Procedures On Cypher) de Neo4j permet de se connecter directement à une base SQL en direct via JDBC (apoc.load.jdbc). On écrit une requête Cypher qui va lire les tables SQL en temps réel et créer les nœuds.
    * Avantage : Pas besoin d'exporter de fichiers intermédiaires (CSV).

* Méthode 3 : Les outils de cartographie d'ETL visuels (Neo4j Data Importer ou Talend)
    * Principe : Utilisation d'outils avec interface graphique où l'on glisse-dépose les fichiers sources et où l'on dessine les flèches pour indiquer au logiciel comment transformer les colonnes en nœuds et relations.
    * Avantage : Ne nécessite quasiment aucune compétence en code (No-Code).

# 2. L'ajout de nouvelles données : L'adjacence des communes/départements

Le cahier des charges demande de prévoir l'enrichissement des données avec des sources publiques (open data), notamment les adjacences géographiques (qui est voisin de qui). L'objectif est de pouvoir analyser la propagation géographique d'un type de délit. Voici comment cela se traduit dans les deux technologies :

Dans la Base de Données Relationnelle (SQL)
Pour ajouter l'adjacence, le SQL exige une modification du schéma (MCD/MLD) et la création d'une nouvelle table d'association réflexive :
```
CREATE TABLE Departement_Voisin (
    code_dept_1 VARCHAR(3),
    code_dept_2 VARCHAR(3),
    PRIMARY KEY (code_dept_1, code_dept_2),
    FOREIGN KEY (code_dept_1) REFERENCES Departement(code_dept),
    FOREIGN KEY (code_dept_2) REFERENCES Departement(code_dept)
);
```
Inconvénient : Pour trouver si un crime s'est propagé sur des départements voisins jusqu'à 3 niveaux de profondeur (le voisin du voisin du voisin), le SQL imposera d'écrire 3 jointures récursives (des JOIN sur la même table). C'est extrêmement coûteux en performances et illisible.

Dans la Base de Données Orientée Graphe (Neo4j)

C'est ici que le graphe brille. Aucun changement de schéma n'est requis. Si l'on dispose d'un simple fichier CSV indiquant dept_A, dept_B, il suffit d'ajouter une relation [:EST_VOISIN_DE] entre les nœuds départements existants.

```
// Exemple de requête d'ajout de l'adjacence
LOAD CSV WITH HEADERS FROM "file:///adjacences.csv" AS ligne
MATCH (d1:Departement {code: ligne.dept_A})
MATCH (d2:Departement {code: ligne.dept_B})
MERGE (d1)-[:EST_VOISIN_DE]-(d2)
```

Avantage : Une fois la flèche créée, répondre à la question de la "propagation" devient natif et quasi immédiat. En Cypher, on peut chercher des chemins de profondeur variable d'une simple ligne :
MATCH (s:Service)-[:A_ENREGISTRE]->(:Infraction {libelle: "Trafic de stupéfiants"})
MATCH (s)-[:SITUE_DANS]->(d1:Departement)-[:EST_VOISIN_DE*1..3]-(d2:Departement)
Ici, *1..3 demande au moteur de naviguer tout seul jusqu'aux voisins de niveau 3, chose redoutable à faire en relationnel !