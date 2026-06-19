import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'projet_2k26_secret'
DB_PATH = os.path.join(os.path.dirname(__file__), 'universite.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # MODIFICATION : Suppression des 'DROP TABLE'. On utilise IF NOT EXISTS pour garder les données.
    cursor.execute('''CREATE TABLE IF NOT EXISTS etudiants (id TEXT PRIMARY KEY, nom TEXT, mention TEXT, mdp TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS notes (id TEXT, matiere TEXT, note REAL, semestre TEXT, annee TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS admins (id TEXT PRIMARY KEY, password TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS configuration (periode_active TEXT)''')
    
    # Insertion des admins uniquement si la table est vide
    cursor.execute("SELECT count(*) FROM admins")
    if cursor.fetchone()[0] == 0:
        admins = [('admin1', '123'), ('admin2', '123'), ('admin3', '123')]
        cursor.executemany('INSERT INTO admins VALUES (?, ?)', admins)
    
    # Valeur par défaut config
    cursor.execute("SELECT count(*) FROM configuration")
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO configuration (periode_active) VALUES ("FERME")')
    
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def est_periode_ouverte():
    conn = get_db()
    periode = conn.execute('SELECT periode_active FROM configuration LIMIT 1').fetchone()
    conn.close()
    return periode['periode_active'] if periode else "FERME"

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifiant = request.form.get('identifiant')
        password = request.form.get('password')
        
        conn = get_db()
        # 1. Vérification Admin dans la base (Plus fiable que "admin"/"admin")
        admin = conn.execute('SELECT * FROM admins WHERE id=? AND password=?', (identifiant, password)).fetchone()
        if admin:
            session['role'] = 'admin'
            conn.close()
            return redirect(url_for('admin_panel'))
            
        # 2. Vérification Étudiant
        etu = conn.execute('SELECT * FROM etudiants WHERE id=? AND mdp=?', (identifiant, password)).fetchone()
        conn.close()
        
        if etu:
            session['role'] = 'etudiant'
            session['user_id'] = identifiant
            return redirect(url_for('releve_notes'))
        else:
            print("Connexion échouée")
            
    return render_template('index.html')

@app.route('/admin')
def admin_panel():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    return render_template('Gestion_admin.html')

@app.route('/ajouter_etudiant', methods=['POST'])
def ajouter_etudiant():
    if session.get('role') != 'admin': return "Accès refusé", 403
    conn = get_db()
    try:
        conn.execute('INSERT INTO etudiants VALUES (?, ?, ?, ?)', 
                     (request.form.get('id'), request.form.get('nom'), request.form.get('mention'), request.form.get('mdp')))
        conn.commit()
    except Exception as e: print(e)
    finally: conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/releve_notes')
def releve_notes():
    if 'user_id' not in session: return redirect(url_for('login'))
    # Vérification période unique
    if est_periode_ouverte() == "FERME": return "Système fermé.", 403
    
    conn = get_db()
    notes = conn.execute('SELECT * FROM notes WHERE id = ? ORDER BY semestre', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('releves_notes.html', notes=notes)

@app.route('/update_periode', methods=['POST'])
def update_periode():
    if session.get('role') != 'admin': return "Accès refusé", 403
    conn = get_db()
    conn.execute('UPDATE configuration SET periode_active = ?', (request.form.get('periode'),))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True)