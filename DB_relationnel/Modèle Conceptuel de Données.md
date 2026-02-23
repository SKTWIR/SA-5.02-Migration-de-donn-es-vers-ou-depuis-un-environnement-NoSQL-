Le MCD permet de visualiser les entités métiers et leurs relations. Nous avons identifié 4 entités principales et 2 associations.

# Les Entités :

   ## DEPARTEMENT : Représente la zone géographique.

        <u>Code_Dept</u> (Identifiant)

   ## SERVICE : Représente le commissariat ou la brigade (ex: CSP BOURG EN BRESSE).

        <u>ID_Service</u> (Identifiant généré)

        Nom_Service

        Perimetre (ex: DCSP, DCCRS)

        Force_Ordre (PN ou GN)

   ## INFRACTION : Le catalogue de l'État 4001 (les 107 types de crimes/délits).

        <u>Code_Index</u> (Identifiant)

        Libelle_Infraction

   ## ANNEE : La dimension temporelle.

        <u>Annee_Valeur</u> (Identifiant)

# Les Associations :

   ## SITUE_DANS : Relie SERVICE (1,1) à DEPARTEMENT (0,n).

        Lecture : Un service est situé dans un et un seul département. Un département contient zéro ou plusieurs services.

   ## ENREGISTRE : Association ternaire (ou table de faits) reliant SERVICE (0,n), INFRACTION (0,n) et ANNEE (0,n).

        Propriété portée par l'association : Nombre_Faits (l'indicateur quantitatif).

        Lecture : Un service enregistre, pour une infraction donnée et une année donnée, un certain nombre de faits.
