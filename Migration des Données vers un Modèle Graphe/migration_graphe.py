import pandas as pd
from neo4j import GraphDatabase
import time

# --- CONFIGURATION DE CONNEXION NEO4J ---
URI = "bolt://localhost:7687"
UTILISATEUR = "neo4j"
MOT_DE_PASSE = "admin123"

def creer_contraintes(driver):
    """Crée des index et des contraintes d'unicité pour accélérer drastiquement la création du graphe"""
    print("⚙️  Création des index et contraintes...")
    requetes = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Departement) REQUIRE d.code IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Infraction) REQUIRE i.code_index IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Service) REQUIRE s.nom IS UNIQUE",
    ]
    with driver.session() as session:
        for req in requetes:
            session.run(req)

def inserer_noeuds(driver, df):
    print("1️⃣  Création des Noeuds : Départements, Infractions et Services...")
    
    # Préparation des listes de dictionnaires uniques
    depts = [{'code': str(d)} for d in df['code_dept'].unique()]
    infras = df[['code_index', 'libelle_infraction']].drop_duplicates().to_dict('records')
    # Pour simplifier l'unicité des services, on concatène le nom et le département
    df['service_unique'] = df['nom_service'] + " (" + df['code_dept'].astype(str) + ")"
    services = df[['service_unique', 'perimetre', 'force_ordre']].drop_duplicates().to_dict('records')

    with driver.session() as session:
        # Insertion des départements
        session.run("""
            UNWIND $depts AS d
            MERGE (:Departement {code: d.code})
        """, depts=depts)
        
        # Insertion des infractions
        session.run("""
            UNWIND $infras AS i
            MERGE (inf:Infraction {code_index: i.code_index})
            ON CREATE SET inf.libelle = i.libelle_infraction
        """, infras=infras)
        
        # Insertion des services
        session.run("""
            UNWIND $services AS s
            MERGE (srv:Service {nom: s.service_unique})
            ON CREATE SET srv.perimetre = s.perimetre, srv.force = s.force_ordre
        """, services=services)

def inserer_relations(driver, df):
    print("2️⃣  Création des Relations (SITUE_DANS et A_ENREGISTRE)...")
    print("⏳ Cette étape peut prendre plusieurs minutes vu le volume de données.")
    
    # Préparation des données pour les relations
    relations_data = df[['service_unique', 'code_dept', 'code_index', 'annee', 'nombre_faits']].to_dict('records')
    
    # On insère par paquets (batches) de 10 000 lignes pour ne pas faire exploser la RAM de Neo4j
    batch_size = 10000
    with driver.session() as session:
        for i in range(0, len(relations_data), batch_size):
            batch = relations_data[i:i+batch_size]
            session.run("""
                UNWIND $batch AS ligne
                
                // 1. Relier le service à son département
                MATCH (s:Service {nom: ligne.service_unique})
                MATCH (d:Departement {code: ligne.code_dept})
                MERGE (s)-[:SITUE_DANS]->(d)
                
                // 2. Relier le service à l'infraction avec l'année et le volume comme propriétés
                MATCH (i:Infraction {code_index: ligne.code_index})
                CREATE (s)-[:A_ENREGISTRE {annee: ligne.annee, nombre_faits: ligne.nombre_faits}]->(i)
            """, batch=batch)
            print(f"Progression : {min(i+batch_size, len(relations_data))} / {len(relations_data)} relations créées...")

if __name__ == "__main__":
    fichier_csv = r"DB_relationnel\base_donnees_propre_2012_2021.csv"
    
    try:
        print(f"📂 Chargement du CSV en mémoire...")
        df_complet = pd.read_csv(fichier_csv, dtype={'code_dept': str, 'nom_service': str}, low_memory=False)
        
        # Filtrer pour retirer les lignes à 0 fait (allège considérablement le graphe)
        df_filtre = df_complet[df_complet['nombre_faits'] > 0].copy()
        
        print(f"🚀 Connexion à Neo4j...")
        driver = GraphDatabase.driver(URI, auth=(UTILISATEUR, MOT_DE_PASSE))
        
        start_time = time.time()
        
        creer_contraintes(driver)
        inserer_noeuds(driver, df_filtre)
        inserer_relations(driver, df_filtre)
        
        driver.close()
        
        duree = round(time.time() - start_time, 2)
        print(f"✅ MIGRATION TERMINÉE AVEC SUCCÈS en {duree} secondes !")
        
    except Exception as e:
        print(f"❌ Une erreur s'est produite : {e}")