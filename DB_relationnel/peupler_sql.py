import pandas as pd
import sqlite3
import os

def peupler_base_sql(fichier_csv, fichier_db):
    print(f"📂 Lecture du fichier {fichier_csv}...")
    # Chargement des données propres
    df = pd.read_csv(fichier_csv)
    
    # Connexion à la base de données SQLite (crée le fichier s'il n'existe pas)
    conn = sqlite3.connect(fichier_db)
    cursor = conn.cursor()

    print("⚙️  Création des tables SQL (MLD)...")
    # Suppression des tables si elles existent déjà (pour pouvoir relancer le script à volonté)
    cursor.executescript('''
    DROP TABLE IF EXISTS Fait_Statistique;
    DROP TABLE IF EXISTS Service;
    DROP TABLE IF EXISTS Infraction;
    DROP TABLE IF EXISTS Departement;

    CREATE TABLE Departement (
        code_dept TEXT PRIMARY KEY
    );

    CREATE TABLE Service (
        id_service INTEGER PRIMARY KEY AUTOINCREMENT,
        nom_service TEXT NOT NULL,
        perimetre TEXT,
        force_ordre TEXT,
        code_dept TEXT,
        FOREIGN KEY (code_dept) REFERENCES Departement(code_dept)
    );

    CREATE TABLE Infraction (
        code_index INTEGER PRIMARY KEY,
        libelle_infraction TEXT NOT NULL
    );

    CREATE TABLE Fait_Statistique (
        id_service INTEGER,
        code_index INTEGER,
        annee_valeur INTEGER,
        nombre_faits INTEGER DEFAULT 0,
        PRIMARY KEY (id_service, code_index, annee_valeur),
        FOREIGN KEY (id_service) REFERENCES Service(id_service),
        FOREIGN KEY (code_index) REFERENCES Infraction(code_index)
    );
    ''')

    # --- 1. Insertion des Départements ---
    print("1️⃣  Insertion des Départements...")
    df_dept = df[['code_dept']].drop_duplicates().dropna()
    df_dept.to_sql('Departement', conn, if_exists='append', index=False)

    # --- 2. Insertion des Infractions ---
    print("2️⃣  Insertion des Infractions (Nomenclature 4001)...")
    df_infraction = df[['code_index', 'libelle_infraction']].drop_duplicates(subset=['code_index']).dropna()
    df_infraction.to_sql('Infraction', conn, if_exists='append', index=False)

    # --- 3. Insertion des Services ---
    print("3️⃣  Insertion des Services (Commissariats et Brigades)...")
    df_service = df[['nom_service', 'perimetre', 'force_ordre', 'code_dept']].drop_duplicates().dropna()
    # L'ID sera généré automatiquement grâce à AUTOINCREMENT
    df_service.to_sql('Service', conn, if_exists='append', index=False)

    # --- 4. Insertion des Faits Statistiques ---
    print("4️⃣  Préparation de la table des Faits Statistiques...")
    # Pour faire la jointure, on doit récupérer les ID générés par la base de données pour les services
    services_db = pd.read_sql_query("SELECT id_service, nom_service, code_dept, force_ordre FROM Service", conn)
    
    # On fusionne pour rapatrier le bon 'id_service' sur chaque ligne de notre gros CSV
    df_merged = df.merge(services_db, on=['nom_service', 'code_dept', 'force_ordre'], how='left')
    
    # On isole uniquement les colonnes nécessaires pour la table finale
    df_faits = df_merged[['id_service', 'code_index', 'annee', 'nombre_faits']].copy()
    df_faits.rename(columns={'annee': 'annee_valeur'}, inplace=True)
    
    # Sécurité : on regroupe au cas où il y aurait des doublons stricts dans les données d'origine
    df_faits = df_faits.groupby(['id_service', 'code_index', 'annee_valeur'], as_index=False)['nombre_faits'].sum()

    print(f"⏳ Insertion de {len(df_faits)} lignes de statistiques (cela peut prendre 1 à 2 minutes)...")
    df_faits.to_sql('Fait_Statistique', conn, if_exists='append', index=False)

    # --- 5. Optimisation ---
    print("⚡ Création des index pour accélérer les requêtes...")
    cursor.executescript('''
    CREATE INDEX idx_stat_annee ON Fait_Statistique(annee_valeur);
    CREATE INDEX idx_stat_service ON Fait_Statistique(id_service);
    CREATE INDEX idx_stat_infraction ON Fait_Statistique(code_index);
    ''')

    conn.commit()
    conn.close()
    
    taille_mo = os.path.getsize(fichier_db) / (1024 * 1024)
    print(f"\n✅ TERMINÉ ! La base SQL '{fichier_db}' a été créée avec succès ({taille_mo:.2f} Mo).")

if __name__ == "__main__":
    csv_entree = "base_donnees_propre_2012_2021.csv"
    base_sortie = "crimes_delits.db"
    
    if os.path.exists(csv_entree):
        peupler_base_sql(csv_entree, base_sortie)
    else:
        print(f"❌ Erreur : Le fichier {csv_entree} est introuvable.")
