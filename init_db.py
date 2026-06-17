import sqlite3

def init_db():
    conn = sqlite3.connect('universite.db')
    cursor = conn.cursor()
    # Création de la table des étudiants
    cursor.execute('''CREATE TABLE IF NOT EXISTS etudiants 
                      (id TEXT PRIMARY KEY, nom TEXT, mention TEXT, mdp TEXT)''')
    # Création de la table des notes
    cursor.execute('''CREATE TABLE IF NOT EXISTS notes 
                      (id TEXT, matiere TEXT, note REAL, annee TEXT)''')
    conn.commit()
    conn.close()
    print("Base de données créée avec succès !")

if __name__ == '__main__':
    init_db()