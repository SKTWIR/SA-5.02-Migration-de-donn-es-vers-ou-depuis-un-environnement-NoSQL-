Le MLD est la traduction du MCD en tables relationnelles (avec clés primaires soulignées et clés étrangères précédées d'un # ou en italique).

  #  Departement (<u>code_dept</u>)

  # Service (<u>id_service</u>, nom_service, perimetre, force_ordre, #code_dept)

  #  Infraction (<u>code_index</u>, libelle_infraction)

   # Fait_Statistique (#id_service, #code_index, #annee_valeur, nombre_faits)
          Note : La clé primaire de cette table est composite, elle est formée par la réunion des trois clés étrangères.
