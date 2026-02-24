# Étude des données et identification des entités et relations clés

L’objectif premier de cette phase a été d'analyser la structure des données brutes (fichiers Excel/CSV fournis par le Ministère de l'Intérieur) afin de concevoir un modèle relationnel normalisé, exempt de redondances et optimisé pour l'interrogation.
# 1. Analyse de la structure initiale (Les données brutes)

L'étude des fichiers sources a révélé une structure en "tableau croisé" (format Wide), conçue pour la lecture humaine mais inadaptée à un Système de Gestion de Base de Données (SGBD).
Les lignes définissaient les types d’infractions (via la nomenclature de l'État 4001, avec un index et un libellé).
Les colonnes et leurs en-têtes imbriqués sur trois niveaux définissaient l'organisation géographique et administrative : l'année, le département, le périmètre (ex: DCSP, DCCRS) et le nom du service (ex: Commissariat ou Brigade).

Les valeurs à l'intersection représentaient le volume (le nombre de faits constatés).

# 2. Identification des Entités (Concepts métiers indépendants)

Pour passer de cette matrice à un Modèle Conceptuel de Données (MCD), nous avons appliqué les règles de normalisation pour isoler les concepts "autonomes". Nous avons identifié trois entités dimensionnelles principales :

* L'entité INFRACTION : Elle représente le "Quoi". Elle est structurée autour d'un identifiant naturel fort (l'Index 4001, allant de 1 à 107) et d'une description textuelle (le libellé du crime ou délit).

* L'entité SERVICE : Elle représente le "Qui". Chaque colonne de nos fichiers correspondait à un point d'enregistrement (une brigade de Gendarmerie ou un commissariat de Police). Cette entité possède ses propres attributs : son nom, son périmètre administratif et son appartenance (Force de l'ordre : PN ou GN).

* L'entité DÉPARTEMENT : Elle représente le "Où". Bien qu'elle n'ait qu'un code dans les données initiales, c'est une entité géographique à part entière qui a vocation à être enrichie ultérieurement (notamment via des données publiques lors du passage au modèle Graphe).

# 3. Identification des Relations et de la Table de Faits

Une fois les entités définies, il a fallu établir comment elles interagissaient pour former l'information finale (le nombre de crimes/délits).

* Relation structurelle (SITUE_DANS) : L'analyse a montré qu'un service appartient de manière stricte à une zone géographique. Nous avons donc identifié une relation (1,1) entre SERVICE et DÉPARTEMENT. Dans le modèle logique, cela se traduit par la présence de la clé étrangère code_dept dans la table des Services.

* Relation événementielle / Table de Faits (ENREGISTRE) : L'information centrale (le "nombre de faits") n'appartient ni à un service seul, ni à une infraction seule, mais résulte du croisement entre un SERVICE, une INFRACTION et une ANNÉE spécifique. Nous avons donc identifié une association ternaire. Dans notre modèle logique relationnel, elle prend la forme d'une table de faits que nous avons nommée Fait_Statistique. Sa clé primaire est composite (ID_Service + Code_Index + Annee), garantissant l'unicité de chaque relevé statistique.

# Conclusion de l'étude conceptuelle

Ce raisonnement analytique nous a permis de concevoir une architecture en "schéma en étoile". Ce modèle relationnel normalisé en 3NF (Troisième Forme Normale) assure l'intégrité des données historiques (2012-2021) tout en préparant naturellement le terrain pour la Phase 3 : en effet, les entités identifiées deviendront les Nœuds (Nodes) de notre future base de données orientée graphe (Neo4j), et les associations deviendront nos Relations (Edges).
