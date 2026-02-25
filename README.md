# SAÉ 5.02 - Migration d'une Base Relationnelle vers un Modèle Graphe (Neo4j)

Ce projet a été réalisé dans le cadre de la **SAÉ 5.02**. Il a pour objectif de modéliser, nettoyer et migrer un jeu de données massives (les statistiques des crimes et délits en France de 2012 à 2021) depuis un format tabulaire brut vers une **Base de Données Relationnelle (SQLite)**, puis de migrer ces données vers une **Base de Données orientée Graphe (Neo4j)** afin d'optimiser les analyses géographiques et temporelles.



## 📋 Contexte et Objectifs

Les données sources proviennent du Ministère de l'Intérieur (Gendarmerie et Police nationales) et recensent 107 types d'infractions (nomenclature *État 4001*). 
L'objectif technique est de démontrer les limites du modèle relationnel (jointures complexes et coûteuses pour l'analyse en réseau) et d'exploiter la puissance du modèle Graphe (*Index-Free Adjacency*) pour répondre instantanément à des requêtes analytiques complexes.

### Les 5 phases du projet :
1. **Analyse et Modélisation** : Nettoyage des données brutes (ETL) et création du modèle logique relationnel.
2. **Analyse des limites** : Étude des contraintes du SQL face aux requêtes analytiques spatiales.
3. **Migration vers Neo4j** : Transformation de la table de faits en relations Graphe.
4. **Validation et Exploitation** : Comparaison des performances Cypher vs SQL.
5. **Documentation** : Rédaction du rapport et ajout de métadonnées géographiques (adjacences).

---

## 🛠️ Technologies Utilisées
* **Langage** : Python 3
* **Librairies** : `pandas` (ETL), `sqlite3` (SQL), `neo4j` (Driver Graphe), `json` (Typage natif)
* **Bases de données** : SQLite (Relationnel) & Neo4j Desktop v1.5.9 (Graphe)
* **Langages de requêtes** : SQL & Cypher

---

## 📂 Architecture du Projet

Le dépôt contient les scripts suivants, à exécuter dans l'ordre chronologique du pipeline de données :

* `Migration_xlsx_csv.py` : Script ETL qui lit le fichier Excel brut (matrices croisées), fusionne les en-têtes complexes, dépivote les tableaux et génère un fichier plat propre (`base_donnees_propre_2012_2021.csv`).
* `peupler_sql.py` : Script qui crée l'architecture relationnelle (3NF) et peuple automatiquement la base de données `crimes_delits.db` (SQLite).
* `migration_graphe.py` : Script de migration massif vers Neo4j. Il contourne les conflits de types (Pandas/Neo4j) et injecte les nœuds et relations par lots de 10 000 via des requêtes Cypher optimisées.

---

## 🚀 Installation et Exécution

### Prérequis
1. Avoir **Python 3** installé.
2. Installer les dépendances Python :
   ```bash
   pip install pandas openpyxl neo4j
3. Avoir installé Neo4j Desktop et démarré une base de données locale (bolt://localhost:7687).

## Étape 1 : Nettoyage des données (ETL)

Placez le fichier Excel source dans le dossier, puis lancez :
```Bash
python Migration_xlsx_csv.py
```
-> Génère un CSV propre de plusieurs millions de lignes.

# Étape 2 : Création de la base de données Relationnelle
```Bash
python peupler_sql.py
```
-> Génère le fichier crimes_delits.db interrogeable via DBeaver ou DB Browser for SQLite.

# Étape 3 : Migration vers le Graphe (neo4j)
*Attention* il est nécessaire de modifiez la variable MOT_DE_PASSE dans le script avec celui de votre instance Neo4j locale avant de lancer : 
```
python migration_graphe.py
```

# Modélisation des Données
## Le modèle Graphe (cible)

La transformation majeur de ce projet a été la suppression de la table des faits SQL.
Au lieu de créer un noeud intermédiaire pour les statistiques, l'information a été transformée en propriétés de la relationn : 
 * (:Service) - [:SITUE_DANS] -> (:Departement)
 * (:Service) - [:A_ENREGISTRE {annee: 2021, nombre_faits: 15}] -> (:Infraction)

# Exemple de requetes (comparaison)

**Objectif** : trouver le type de crime le plus fréquent par département. 

En SQL :
```SQL
WITH TotalParDeptEtCrime AS (
    SELECT s.code_dept, i.libelle_infraction, SUM(f.nombre_faits) AS total_faits
    FROM Fait_Statistique f
    JOIN Service s ON f.id_service = s.id_service
    JOIN Infraction i ON f.code_index = i.code_index
    GROUP BY s.code_dept, i.libelle_infraction
),
Classement AS (
    SELECT code_dept, libelle_infraction, total_faits,
           ROW_NUMBER() OVER(PARTITION BY code_dept ORDER BY total_faits DESC) as rang
    FROM TotalParDeptEtCrime
)
SELECT code_dept, libelle_infraction, total_faits FROM Classement WHERE rang = 1;
```
la requete est complexe, verbeux et nécessite 3 jointure et du fenetrage

En Cypher sur Neo4j :
```Cypher
MATCH (d:Departement)<-[:SITUE_DANS]-(s:Service)-[e:A_ENREGISTRE]->(i:Infraction)
WITH d.code AS Dept, i.libelle AS Crime, SUM(e.nombre_faits) AS Total
ORDER BY Total DESC
WITH Dept, collect({crime: Crime, total: Total})[0] AS TopCrime
RETURN Dept, TopCrime.crime, TopCrime.total
ORDER BY TopCrime.total DESC LIMIT 10;
```
la requete est intuitif et suit naturellement le réseau imaginé grace au modèle de graphe

