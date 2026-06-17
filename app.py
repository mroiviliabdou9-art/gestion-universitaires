import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'cle_secrete_universite_2026'

# Configuration simple pour Render
DB_FILE = 'gestion_univ.db'

def get_db_connection():
    # Timeout ajouté pour éviter les blocages de base de données
    conn = sqlite3.connect(DB_FILE, timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Création des tables nécessaires
    conn.execute('''CREATE TABLE IF NOT EXISTS utilisateurs (
                    id_utilisateur TEXT PRIMARY KEY, 
                    nom TEXT NOT NULL, 
                    mot_de_passe TEXT NOT NULL, 
                    role TEXT NOT NULL)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS notes (
                    id_etudiant TEXT, 
                    matiere TEXT, 
                    note REAL)''')

    # Initialisation des 3 admins demandés
    admins = [
        ('ADM_01', 'Admin Principal', 'admin123', 'admin'),
        ('ADM_02', 'Admin Secondaire', 'admin456', 'admin'),
        ('ADM_03', 'Admin Technique', 'admin789', 'admin')
    ]
    for admin in admins:
        conn.execute('INSERT OR IGNORE INTO utilisateurs VALUES (?, ?, ?, ?)', admin)
    
    conn.commit()
    conn.close()

# Initialisation au lancement
init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_id = request.form.get('identifiant', '').strip()
        password = request.form.get('password', '').strip()
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM utilisateurs WHERE id_utilisateur = ? AND mot_de_passe = ?', 
                            (user_id, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id_utilisateur']
            session['nom'] = user['nom']
            session['role'] = user['role']
            # Redirection selon le rôle
            if user['role'] == 'admin':
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('releve_notes'))
        else:
            flash("Identifiant ou mot de passe incorrect.")
            
    return render_template('index.html')

@app.route('/admin')
def admin():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('index'))
    return render_template('Gestion_admin.html')

@app.route('/ajouter_etudiant', methods=['POST'])
def ajouter_etudiant():
    # Récupère les données du formulaire Gestion_admin.html
    id_etu = request.form.get('id_etudiant')
    nom = request.form.get('nom')
    mdp = request.form.get('mot_de_passe')
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO utilisateurs (id_utilisateur, nom, mot_de_passe, role) VALUES (?, ?, ?, ?)', 
                     (id_etu, nom, mdp, 'etudiant'))
        conn.commit()
        flash("Étudiant ajouté avec succès !")
    except:
        flash("Erreur : Cet ID existe déjà.")
    conn.close()
    return redirect(url_for('admin'))

@app.route('/ajouter_note', methods=['POST'])
def ajouter_note():
    # Récupère les données du formulaire Gestion_admin.html
    id_etu = request.form.get('id_etudiant')
    matiere = request.form.get('matiere')
    note = request.form.get('note')
    
    conn = get_db_connection()
    conn.execute('INSERT INTO notes (id_etudiant, matiere, note) VALUES (?, ?, ?)', 
                 (id_etu, matiere, note))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/releve_notes')
def releve_notes():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    notes = conn.execute('SELECT * FROM notes WHERE id_etudiant = ?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('releves_notes.html', notes=notes)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run()