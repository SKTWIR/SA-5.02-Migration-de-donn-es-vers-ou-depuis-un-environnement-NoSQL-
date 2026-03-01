import pandas as pd

def nettoyer_excel_complet(nom_fichier):
    print(f"Chargement du fichier Excel : {nom_fichier}")
    print("Cela peut prendre 1 à 2 minutes vu la taille du fichier")
    
    # Chargement de tous les onglets
    xls = pd.read_excel(nom_fichier, sheet_name=None, header=None)
    
    toutes_les_donnees = []

    for nom_onglet, df in xls.items():
        # --- CORRECTION ICI : On ignore les onglets de présentation/documentation ---
        if "Services" not in nom_onglet:
            print(f"Ignoré : l'onglet '{nom_onglet}' n'est pas un onglet de données.")
            continue
            
        print(f"Traitement de l'onglet : {nom_onglet}")
        
        # 1. Déduction de la force de l'ordre et de l'année
        force = "PN" if "PN" in nom_onglet else "GN"
        annee = [mot for mot in nom_onglet.replace("-", " ").split() if mot.isdigit() and len(mot) == 4]
        annee = int(annee[0]) if annee else 0

        # 2. Extraction des en-têtes (on gère les cas d'onglets un peu différents)
        try:
            departements = df.iloc[0, 2:].ffill() 
            perimetres = df.iloc[1, 2:].fillna("Non Renseigné")
            noms_service = df.iloc[2, 2:].fillna("Non Renseigné")
        except Exception as e:
            print(f"Erreur de structure sur l'onglet {nom_onglet}, ignoré.")
            continue
        
        # 3. Données des infractions
        donnees = df.iloc[3:].copy()
        donnees.rename(columns={0: 'code_index', 1: 'libelle_infraction'}, inplace=True)
        
        # 4. Dépivotage
        df_fondu = donnees.melt(
            id_vars=['code_index', 'libelle_infraction'], 
            var_name='col_index', 
            value_name='nombre_faits'
        )
        
        # 5. Mapping
        mapping = pd.DataFrame({
            'col_index': df.columns[2:],
            'code_dept': departements.values,
            'perimetre': perimetres.values,
            'nom_service': noms_service.values
        })
        
        # 6. Fusion
        df_propre = pd.merge(df_fondu, mapping, on='col_index')
        
        # 7. Métadonnées
        df_propre['annee'] = annee
        df_propre['force_ordre'] = force
        
        # 8. Nettoyage final
        df_propre.drop(columns=['col_index'], inplace=True)
        df_propre['nombre_faits'] = pd.to_numeric(df_propre['nombre_faits'], errors='coerce').fillna(0).astype(int)
        df_propre['code_index'] = pd.to_numeric(df_propre['code_index'], errors='coerce')
        
        df_propre = df_propre.dropna(subset=['code_index'])
        df_propre['code_index'] = df_propre['code_index'].astype(int)
        
        toutes_les_donnees.append(df_propre)

    # Concaténation et sauvegarde
    if toutes_les_donnees:
        df_final = pd.concat(toutes_les_donnees, ignore_index=True)
        fichier_sortie = r"DB_relationnel\base_donnees_propre_2012_2021.csv"
        df_final.to_csv(fichier_sortie, index=False, encoding='utf-8')
        print(f"\n✅ Nettoyage terminé avec succès !")
        print(f"Fichier plat généré : {fichier_sortie} (Total : {len(df_final)} lignes)")
    else:
        print("Erreur : Aucune donnée n'a pu être extraite.")

if __name__ == "__main__":
    # Assurez-vous que le chemin est correct (avec des doubles anti-slash \\ ou un r devant les guillemets)
    nom_du_fichier = r"Consige_et_donnees_brut\crimes-et-delits-enregistres-par-les-services-de-gendarmerie-et-de-police-depuis-2012.xlsx"
    nettoyer_excel_complet(nom_du_fichier)