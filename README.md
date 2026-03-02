# SAÉ 5.02 - Migration d'une Base de Données Relationnelle vers un Modèle Graphe (Neo4j)

Ce projet a été réalisé dans le cadre de la **SAÉ 5.02** et répond à la demande du Ministère de l'Intérieur[cite: 3, 4]. Il a pour objectif principal d'optimiser l'analyse des données relatives aux crimes et délits enregistrés par la Police et la Gendarmerie nationale[cite: 9, 14, 23]. 

Le projet consiste à modéliser un jeu de données massives depuis un format tabulaire brut vers une **Base de Données Relationnelle (SQLite)**, puis de migrer ces données vers une **Base de Données orientée Graphe (Neo4j)**. Les bases de données relationnelles présentant des limites pour les analyses complexes en réseau[cite: 10], l'utilisation du modèle Graphe (*Index-Free Adjacency*) permet de répondre instantanément à des requêtes analytiques spatiales et temporelles.

## Contexte et Objectifs

Les données sources proviennent du Ministère de l'Intérieur et recensent 107 types d'infractions. Conformément au cahier des charges, le projet s'articule autour de 5 grandes phases :

1.  **Phase 1 : Analyse des Données Sources et Modélisation Relationnel** (Nettoyage ETL et création du MCD/MLD)[cite: 22].
2.  **Phase 2 : Analyse des Limites du modèle relationnel** (Étude des contraintes SQL face aux requêtes analytiques)[cite: 28].
3.  **Phase 3 : Migration des Données vers un Modèle Graphe** (Transformation de la base SQL en réseau Neo4j v1.5.9)[cite: 32, 34].
4.  **Phase 4 : Validation et Exploitation de la Solution Graphe** (Comparaison des performances Cypher vs SQL)[cite: 35].
5.  **Phase 5 : Rédaction et Présentation du Rapport Final** (Documentation et enrichissement via des données publiques)[cite: 18, 41].

---

## Technologies Utilisées

* **Langage** : Python 3
* **Librairies** : `pandas` (ETL), `sqlite3` (SQL natif), `neo4j` (Driver Graphe), `requests` (API Web Sémantique)
* **Bases de données** : SQLite (Relationnel) & Neo4j Desktop v1.5.9 (Graphe) [cite: 34]
* **Langages de requêtes** : SQL & Cypher

---

## Architecture du Projet

Le dépôt contient les scripts suivants, à exécuter dans l'ordre chronologique du pipeline de données :

* `Migration_xlsx_csv.py` : Script ETL qui lit le fichier Excel brut (matrices croisées), fusionne les en-têtes complexes, dépivote les tableaux et génère un fichier plat propre.
* `peupler_sql.py` : Script qui crée l'architecture relationnelle (3NF) et peuple automatiquement la base de données `crimes_delits.db` (SQLite) dans le dossier `DB_relationnel/`.
* `migration_sql_vers_graphe.py` : Script de migration directe "Base-à-Base". Il interroge la base SQLite et injecte massivement les nœuds et relations dans Neo4j par lots (Batch) via des requêtes Cypher optimisées.
* `enrichir_graphe.py` : Script d'enrichissement géographique qui interroge l'API du Gouvernement (`geo.api.gouv.fr`) pour intégrer les Régions et relie les départements limitrophes via un dictionnaire de frontières.

---

## Installation et Exécution

### Prérequis
1. Avoir **Python 3** installé sur votre machine.
2. Installer les dépendances Python requises :
   ```bash
   pip install pandas openpyxl neo4j requests