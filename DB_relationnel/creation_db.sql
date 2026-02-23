-- 1. Table des Départements
CREATE TABLE Departement (
    code_dept VARCHAR(3) PRIMARY KEY
);

-- 2. Table des Services de Police/Gendarmerie
CREATE TABLE Service (
    id_service SERIAL PRIMARY KEY, -- Mettre INT AUTO_INCREMENT si vous utilisez MySQL/MariaDB
    nom_service VARCHAR(255) NOT NULL,
    perimetre VARCHAR(150),
    force_ordre VARCHAR(2), -- 'PN' ou 'GN'
    code_dept VARCHAR(3),
    FOREIGN KEY (code_dept) REFERENCES Departement(code_dept)
);

-- 3. Table des Infractions (Index Etat 4001)
CREATE TABLE Infraction (
    code_index INT PRIMARY KEY,
    libelle_infraction VARCHAR(255) NOT NULL
);

-- 4. Table de Faits (Statistiques Annuelles)
CREATE TABLE Fait_Statistique (
    id_service INT,
    code_index INT,
    annee_valeur INT,
    nombre_faits INT DEFAULT 0,
    PRIMARY KEY (id_service, code_index, annee_valeur),
    FOREIGN KEY (id_service) REFERENCES Service(id_service),
    FOREIGN KEY (code_index) REFERENCES Infraction(code_index)
);

-- Index pour optimiser les futures requêtes d'analyse
CREATE INDEX idx_stat_annee ON Fait_Statistique(annee_valeur);
CREATE INDEX idx_stat_service ON Fait_Statistique(id_service);
