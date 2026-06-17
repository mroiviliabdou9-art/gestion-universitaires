from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'une_cle_secrete_tres_sure' # Change ceci pour la production

def get_db_connection():
    conn = sqlite3.connect('gestion_univ.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Création des tables
    conn.execute('CREATE TABLE IF NOT EXISTS utilisateurs (id_utilisateur TEXT PRIMARY KEY, nom TEXT, mot_de_passe TEXT, role TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS ecolages (id_etudiant TEXT PRIMARY KEY, statut_paiement INTEGER DEFAULT 0)')
    conn.execute('CREATE TABLE IF NOT EXISTS notes (id_etudiant TEXT, matiere TEXT, note REAL)')
    
    # Création des 3 admins par défaut
    admins = [('ADM_01', 'Admin 1', 'admin123', 'admin'), ('ADM_02', 'Admin 2', 'admin456', 'admin'), ('ADM_03', 'Admin 3', 'admin789', 'admin')]
    for admin in admins:
        conn.execute('INSERT OR IGNORE INTO utilisateurs VALUES (?, ?, ?, ?)', admin)
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifiant = request.form['identifiant']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM utilisateurs WHERE id_utilisateur = ? AND mot_de_passe = ?', (identifiant, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id_utilisateur']
            session['nom'] = user['nom']
            session['role'] = user['role']
            return redirect(url_for('admin_panel' if user['role'] == 'admin' else 'releve_notes'))
        flash("Identifiants incorrects.")
    return render_template('index.html')

@app.route('/admin')
def admin_panel():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    return render_template('Gestion_admin.html')

@app.route('/ajouter_etudiant', methods=['POST'])
def ajouter_etudiant():
    # Logique d'ajout...
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
