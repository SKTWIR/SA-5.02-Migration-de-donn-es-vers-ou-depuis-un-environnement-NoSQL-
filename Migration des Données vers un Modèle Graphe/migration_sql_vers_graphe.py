import sqlite3
from neo4j import GraphDatabase
import time

# --- CONFIGURATION NEO4J ---
URI = "bolt://localhost:7687"
UTILISATEUR = "neo4j"
MOT_DE_PASSE = "VOTRE_MOT_DE_PASSE_ICI" # <-- À MODIFIER

# --- CONFIGURATION SQLITE ---
DB_SQLITE = "crimes_delits.db"

def vider_graphe(neo_driver):
    print("🧹 Nettoyage de la base Neo4j...")
    with neo_driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

def creer_contraintes(neo_driver):
    print("⚙️  Création des index Neo4j...")
    requetes = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Departement) REQUIRE d.code IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Infraction) REQUIRE i.code_index IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Service) REQUIRE s.nom IS UNIQUE",
    ]
    with neo_driver.session() as session:
        for req in requetes:
            try:
                session.run(req)
            except Exception:
                pass

def inserer_noeuds_depuis_sql(neo_driver, sqlite_conn):
    print("1️⃣  Extraction depuis SQLite et Création des Noeuds...")
    cursor = sqlite_conn.cursor()

    # 1. Extraction des Départements
    cursor.execute("SELECT code_dept FROM Departement")
    depts = [{'code': str(row[0])} for row in cursor.fetchall()]

    # 2. Extraction des Infractions
    cursor.execute("SELECT code_index, libelle_infraction FROM Infraction")
    infras = [{'code_index': int(row[0]), 'libelle_infraction': str(row[1])} for row in cursor.fetchall()]

    # 3. Extraction des Services (On recrée notre clé unique "Nom (Dept)")
    cursor.execute("SELECT nom_service || ' (' || code_dept || ')' AS nom, perimetre, force_ordre FROM Service")
    services = [{'nom': str(row[0]), 'perimetre': str(row[1]), 'force_ordre': str(row[2])} for row in cursor.fetchall()]

    with neo_driver.session() as session:
        session.run("UNWIND $depts AS d MERGE (:Departement {code: d.code})", depts=depts)
        session.run("UNWIND $infras AS i MERGE (infra:Infraction {code_index: i.code_index}) SET infra.libelle = i.libelle_infraction", infras=infras)
        session.run("UNWIND $services AS s MERGE (srv:Service {nom: s.nom}) SET srv.perimetre = s.perimetre, srv.force = s.force_ordre", services=services)

def inserer_relations_depuis_sql(neo_driver, sqlite_conn):
    print("2️⃣  Extraction des Statistiques et Création des Relations...")
    cursor = sqlite_conn.cursor()

    # Requête SQL pour préparer nos données de relations.
    # On fait une jointure pour récupérer le nom du service et son département.
    requete_sql = """
    SELECT
        s.nom_service || ' (' || s.code_dept || ')' AS service_unique,
        s.code_dept,
        f.code_index,
        f.annee_valeur AS annee,
        f.nombre_faits
    FROM Fait_Statistique f
    JOIN Service s ON f.id_service = s.id_service
    WHERE f.nombre_faits > 0
    """
    cursor.execute(requete_sql)

    batch_size = 10000
    total_relations = 0

    with neo_driver.session() as session:
        while True:
            # On lit la base SQLite par paquets de 10 000 pour ne pas saturer la RAM
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break # Fin des données

            # Formatage natif Python pour Neo4j
            batch = [
                {
                    'service_unique': str(row[0]),
                    'code_dept': str(row[1]),
                    'code_index': int(row[2]),
                    'annee': int(row[3]),
                    'nombre_faits': int(row[4])
                } for row in rows
            ]

            # Injection Cypher
            session.run("""
                UNWIND $batch AS ligne

                MATCH (s:Service {nom: ligne.service_unique})
                MATCH (d:Departement {code: ligne.code_dept})
                MERGE (s)-[:SITUE_DANS]->(d)

                WITH s, ligne
                MATCH (infra:Infraction {code_index: ligne.code_index})
                CREATE (s)-[:A_ENREGISTRE {annee: ligne.annee, nombre_faits: ligne.nombre_faits}]->(infra)
            """, batch=batch)

            total_relations += len(batch)
            print(f"Progression : {total_relations} relations migrées depuis SQLite...")

if __name__ == "__main__":
    try:
        print(f"🔌 Connexion à la base SQLite ({DB_SQLITE})...")
        sqlite_conn = sqlite3.connect(DB_SQLITE)

        print(f"🚀 Connexion à Neo4j...")
        neo_driver = GraphDatabase.driver(URI, auth=(UTILISATEUR, MOT_DE_PASSE))

        start_time = time.time()

        vider_graphe(neo_driver)
        creer_contraintes(neo_driver)
        inserer_noeuds_depuis_sql(neo_driver, sqlite_conn)
        inserer_relations_depuis_sql(neo_driver, sqlite_conn)

        # Fermeture propre des deux bases de données
        neo_driver.close()
        sqlite_conn.close()

        duree = round(time.time() - start_time, 2)
        print(f"\n✅ MIGRATION DB-VERS-DB TERMINÉE AVEC SUCCÈS en {duree} secondes !")

    except Exception as e:
        print(f"❌ Une erreur s'est produite : {e}")
