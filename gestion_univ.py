import sqlite3

def initialiser_base():
    # Connexion à la base de données (se crée automatiquement)
    conn = sqlite3.connect('gestion_univ.db')
    cursor = conn.cursor()

    print("Création des tables dans la base de données...")

    # 1. Table Administrateurs (Corrigée avec NOT NULL)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS administrateurs (
            id_admin TEXT PRIMARY KEY,
            nom_affichage TEXT NOT NULL,
            mot_de_passe TEXT NOT NULL
        )
    ''')

    # 2. Table Étudiants (Corrigée avec NOT NULL et écolage)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS etudiants (
            id_etudiant TEXT PRIMARY KEY,
            nom_prenom TEXT NOT NULL,
            date_naissance TEXT,
            lieu_naissance TEXT,
            niveau TEXT,
            mot_de_passe TEXT,
            ecolage_paye INTEGER DEFAULT 0  -- 0 = Non payé (bloqué), 1 = Payé (autorisé)
        )
    ''')

    # 3. Table Notes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id_note INTEGER PRIMARY KEY AUTOINCREMENT,
            id_etudiant TEXT,
            matiere TEXT,
            note1 REAL,
            note2 REAL,
            note3 REAL,
            moyenne REAL,
            statut TEXT,
            annee_universitaire TEXT,
            FOREIGN KEY (id_etudiant) REFERENCES etudiants (id_etudiant)
        )
    ''')

    # ========================================================
    # INJECTION DE DONNÉES DE TEST
    # ========================================================
    
    # Compte Admin par défaut
    cursor.execute("SELECT COUNT(*) FROM administrateurs")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO administrateurs VALUES ('ADM_01', 'Mamy (Secrétariat)', 'admin123')")
        print("- Compte Admin créé ! (ID: ADM_01 / MDP: admin123)")

    # Compte Étudiant de test (Mroivil Abdoulkader) - Configuré comme PAYÉ (1)
    cursor.execute("SELECT COUNT(*) FROM etudiants")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO etudiants VALUES 
            ('ETU_001', 'Mroivil Abdoulkader', '2005-04-12', 'Antananarivo', 'L1 Informatique', 'etu123', 1)
        """)
        print("- Compte Étudiant créé ! (ID: ETU_001 / MDP: etu123)")

    # Notes de test correspondantes à ton tableau
    cursor.execute("SELECT COUNT(*) FROM notes")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO notes (id_etudiant, matiere, note1, note2, note3, moyenne, statut, annee_universitaire)
            VALUES ('ETU_001', 'Algorithme', 12.0, 13.0, 10.0, 11.66, 'Validé', '2025-2026')
        """)
        print("- Notes d'Algorithme insérées pour le test !")

    conn.commit()
    conn.close()
    print("\n[SUCCÈS] Le fichier 'gestion_univ.db' a été généré avec succès !")

if __name__ == '__main__':
    initialiser_base()
