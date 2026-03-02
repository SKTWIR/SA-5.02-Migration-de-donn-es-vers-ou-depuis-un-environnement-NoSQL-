import requests
from neo4j import GraphDatabase

# --- CONFIGURATION DE CONNEXION NEO4J ---
URI = "bolt://localhost:7687"
UTILISATEUR = "neo4j"
MOT_DE_PASSE = "admin123" # <-- À adapterr

def telecharger_donnees_gouvernementales():
    """
    Utilise l'API officielle du gouvernement (geo.api.gouv.fr)
    pour récupérer les Régions et leur lien avec les Départements.
    """
    print("Interrogation de l'API geo.api.gouv.fr en cours...")
    
    # 1. Récupération des régions
    reponse_regions = requests.get("https://geo.api.gouv.fr/regions")
    regions_data = reponse_regions.json()
    
    # 2. Récupération des départements (qui contiennent leur codeRegion)
    reponse_depts = requests.get("https://geo.api.gouv.fr/departements")
    depts_data = reponse_depts.json()
    
    print(f"Succès ! {len(regions_data)} régions et {len(depts_data)} départements récupérés en un éclair.")
    return regions_data, depts_data

def enrichir_neo4j_avec_regions(driver, regions, departements):
    print("Création des Noeuds (:Region) et des relations [:APPARTIENT_A]...")
    
    with driver.session() as session:
        # Étape 1 : Créer les nœuds Région
        session.run("""
            UNWIND $regions AS reg
            MERGE (r:Region {code: reg.code})
            SET r.nom = reg.nom
        """, regions=regions)
        
        # Étape 2 : Lier nos Départements existants à ces Régions
        session.run("""
            UNWIND $departements AS dep
            // On cherche notre département existant
            MATCH (d:Departement {code: dep.code})
            // On cherche la région correspondante
            MATCH (r:Region {code: dep.codeRegion})
            // On crée la relation d'appartenance
            MERGE (d)-[:APPARTIENT_A]->(r)
        """, departements=departements)
        
    print("Le graphe a été enrichi avec succès avec les données du Gouvernement !")

if __name__ == "__main__":
    try:
        # Téléchargement instantané via l'API REST
        regions, departements = telecharger_donnees_gouvernementales()
        
        # Injection
        driver = GraphDatabase.driver(URI, auth=(UTILISATEUR, MOT_DE_PASSE))
        enrichir_neo4j_avec_regions(driver, regions, departements)
        driver.close()
        
    except Exception as e:
        print(f"Erreur : {e}")