import pandas as pd
from neo4j import GraphDatabase
import time

# --- CONFIGURATION DE CONNEXION NEO4J ---
URI = "bolt://localhost:7687"
UTILISATEUR = "neo4j"
MOT_DE_PASSE = "admin123" # <-- À MODIFIER

def vider_graphe(driver):
    """Supprime les données corrompues des anciens essais pour repartir de zéro"""
    print("🧹 Nettoyage de la base de données (suppression des anciens essais)...")
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

def creer_contraintes(driver):
    print("⚙️  Création des index et contraintes...")
    requetes = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Departement) REQUIRE d.code IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Infraction) REQUIRE i.code_index IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Service) REQUIRE s.nom IS UNIQUE",
    ]
    with driver.session() as session:
        for req in requetes:
            try:
                session.run(req)
            except Exception:
                pass

def inserer_noeuds(driver, df):
    print("1️⃣  Création des Noeuds : Départements, Infractions et Services...")
    
    # METHODE INFAILLIBLE : Conversion en types natifs Python exclusifs
    depts = [{'code': str(d)} for d in df['code_dept'].unique()]
    
    df_infras = df[['code_index', 'libelle_infraction']].drop_duplicates()
    infras = [
        {'code_index': int(row.code_index), 'libelle_infraction': str(row.libelle_infraction)} 
        for row in df_infras.itertuples(index=False)
    ]
    
    df_services = df[['service_unique', 'perimetre', 'force_ordre']].drop_duplicates()
    services = [
        {'nom': str(row.service_unique), 'perimetre': str(row.perimetre), 'force_ordre': str(row.force_ordre)} 
        for row in df_services.itertuples(index=False)
    ]

    with driver.session() as session:
        session.run("UNWIND $depts AS d MERGE (:Departement {code: d.code})", depts=depts)
        session.run("UNWIND $infras AS i MERGE (inf:Infraction {code_index: i.code_index}) SET inf.libelle = i.libelle_infraction", infras=infras)
        session.run("UNWIND $services AS s MERGE (srv:Service {nom: s.nom}) SET srv.perimetre = s.perimetre, srv.force = s.force_ordre", services=services)

def inserer_relations(driver, df):
    print("2️⃣  Création des Relations (SITUE_DANS et A_ENREGISTRE)...")
    print("⏳ Préparation des données relationnelles en cours...")
    
    # On force la conversion native pour les millions de relations
    df_rels = df[['service_unique', 'code_dept', 'code_index', 'annee', 'nombre_faits']]
    relations_data = [
        {
            'service_unique': str(row.service_unique),
            'code_dept': str(row.code_dept),
            'code_index': int(row.code_index),
            'annee': int(row.annee),
            'nombre_faits': int(row.nombre_faits)
        }
        for row in df_rels.itertuples(index=False)
    ]
    
    batch_size = 10000
    print(f"⏳ Insertion de {len(relations_data)} relations par paquets de {batch_size} (Veuillez patienter)...")
    
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
        print(f"📂 Chargement du CSV...")
        df_complet = pd.read_csv(fichier_csv, dtype=str, keep_default_na=False, low_memory=False)
        
        # Formatage drastique des valeurs
        df_complet['nombre_faits'] = pd.to_numeric(df_complet['nombre_faits'], errors='coerce').fillna(0).astype(int)
        df_complet['code_index'] = pd.to_numeric(df_complet['code_index'], errors='coerce').fillna(0).astype(int)
        df_complet['annee'] = pd.to_numeric(df_complet['annee'], errors='coerce').fillna(0).astype(int)
        
        df_complet['code_dept'] = df_complet['code_dept'].astype(str).str.strip()
        df_complet['nom_service'] = df_complet['nom_service'].astype(str).str.strip()
        df_complet['perimetre'] = df_complet['perimetre'].astype(str).str.strip()
        df_complet['force_ordre'] = df_complet['force_ordre'].astype(str).str.strip()
        df_complet['libelle_infraction'] = df_complet['libelle_infraction'].astype(str).str.strip()
        
        # Création de la clé unique
        df_complet['service_unique'] = df_complet['nom_service'] + " (" + df_complet['code_dept'] + ")"
        
        df_filtre = df_complet[df_complet['nombre_faits'] > 0].copy()
        
        print(f"🚀 Connexion à Neo4j...")
        driver = GraphDatabase.driver(URI, auth=(UTILISATEUR, MOT_DE_PASSE))
        
        start_time = time.time()
        
        # Exécution dans l'ordre stricts
        vider_graphe(driver)
        creer_contraintes(driver)
        inserer_noeuds(driver, df_filtre)
        inserer_relations(driver, df_filtre)
        
        driver.close()
        
        duree = round(time.time() - start_time, 2)
        print(f"\n✅ MIGRATION TERMINÉE AVEC SUCCÈS en {duree} secondes !")
        print("➡️ Allez sur Neo4j Desktop et tapez : MATCH (n) RETURN n LIMIT 50")
        
    except Exception as e:
        print(f"❌ Une erreur s'est produite : {e}")