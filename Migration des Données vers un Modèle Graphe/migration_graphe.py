import pandas as pd
from neo4j import GraphDatabase
import time

# --- CONFIGURATION DE CONNEXION NEO4J ---
URI = "bolt://localhost:7687"
UTILISATEUR = "neo4j"
MOT_DE_PASSE = "admin123"

def creer_contraintes(driver):
    """Crée des index et des contraintes d'unicité pour accélérer la création du graphe"""
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
    
    depts = [{'code': str(d)} for d in df['code_dept'].unique()]
    infras = df[['code_index', 'libelle_infraction']].drop_duplicates().to_dict('records')
    
    # Création d'un identifiant unique pour les services
    df['service_unique'] = df['nom_service'] + " (" + df['code_dept'].astype(str) + ")"
    services = df[['service_unique', 'perimetre', 'force_ordre']].drop_duplicates().to_dict('records')

    with driver.session() as session:
        # Départements
        session.run("""
            UNWIND $depts AS d
            MERGE (:Departement {code: d.code})
        """, depts=depts)
        
        # Infractions
        session.run("""
            UNWIND $infras AS i
            MERGE (inf:Infraction {code_index: i.code_index})
            ON CREATE SET inf.libelle = i.libelle_infraction
        """, infras=infras)
        
        # Services
        session.run("""
            UNWIND $services AS s
            MERGE (srv:Service {nom: s.service_unique})
            ON CREATE SET srv.perimetre = s.perimetre, srv.force = s.force_ordre
        """, services=services)

def inserer_relations(driver, df):
    print("2️⃣  Création des Relations (SITUE_DANS et A_ENREGISTRE)...")
    print("⏳ Cette étape peut prendre 1 à 3 minutes vu le volume de données.")
    
    relations_data = df[['service_unique', 'code_dept', 'code_index', 'annee', 'nombre_faits']].to_dict('records')
    
    batch_size = 10000
    with driver.session() as session:
        for i in range(0, len(relations_data), batch_size):
            batch = relations_data[i:i+batch_size]
            session.run("""
                UNWIND $batch AS ligne
                
                MATCH (s:Service {nom: ligne.service_unique})
                MATCH (d:Departement {code: ligne.code_dept})
                MERGE (s)-[:SITUE_DANS]->(d)
                
                WITH s, ligne
                MATCH (inf:Infraction {code_index: ligne.code_index})
                CREATE (s)-[:A_ENREGISTRE {annee: ligne.annee, nombre_faits: ligne.nombre_faits}]->(inf)
            """, batch=batch)
            print(f"Progression : {min(i+batch_size, len(relations_data))} / {len(relations_data)} relations créées...")

if __name__ == "__main__":
    fichier_csv = r"DB_relationnel\base_donnees_propre_2012_2021.csv"
    
    try:
        print(f"📂 Chargement du CSV et nettoyage rigoureux des types...")
        
        # 1. On charge tout en texte pour bloquer l'apparition de Float/NaN non désirés
        df_complet = pd.read_csv(fichier_csv, dtype=str, keep_default_na=False, low_memory=False)
        
        # 2. Conversion sécurisée des nombres (si erreur ou vide -> 0)
        df_complet['nombre_faits'] = pd.to_numeric(df_complet['nombre_faits'], errors='coerce').fillna(0).astype(int)
        df_complet['code_index'] = pd.to_numeric(df_complet['code_index'], errors='coerce').fillna(0).astype(int)
        df_complet['annee'] = pd.to_numeric(df_complet['annee'], errors='coerce').fillna(0).astype(int)
        
        # 3. Nettoyage et verrouillage des textes
        df_complet['code_dept'] = df_complet['code_dept'].astype(str).str.strip()
        df_complet['nom_service'] = df_complet['nom_service'].astype(str).str.strip()
        df_complet['perimetre'] = df_complet['perimetre'].astype(str).str.strip()
        df_complet['force_ordre'] = df_complet['force_ordre'].astype(str).str.strip()
        df_complet['libelle_infraction'] = df_complet['libelle_infraction'].astype(str).str.strip()
        
        # 4. On supprime les faits à 0 pour alléger drastiquement le graphe
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