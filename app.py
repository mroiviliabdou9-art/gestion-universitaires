import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'projet_2k26_secret'

# Chemin absolu pour la base de données (indispensable pour Render)
DB_PATH = os.path.join(os.path.dirname(__file__), 'universite.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- CONNEXION UNIQUE ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifiant = request.form.get('identifiant')
        password = request.form.get('password')
        
        # Test Admin
        if identifiant == 'admin' and password == 'admin':
            session['role'] = 'admin'
            return redirect(url_for('admin_panel'))
        
        # Test Étudiant
        conn = get_db()
        etu = conn.execute('SELECT * FROM etudiants WHERE id=? AND mdp=?', (identifiant, password)).fetchone()
        conn.close()
        
        if etu:
            session['role'] = 'etudiant'
            session['user_id'] = identifiant
            return redirect(url_for('releve_notes'))
            
    return render_template('index.html')

@app.route('/admin')
def admin_panel():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    return render_template('Gestion_admin.html')

@app.route('/releve_notes')
def releve_notes():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    # Calcul dynamique : Matière | Liste des notes | Moyenne
    notes = conn.execute('''SELECT matiere, GROUP_CONCAT(note, ', ') as liste_notes, 
                            AVG(note) as moyenne FROM notes WHERE id = ? 
                            GROUP BY matiere''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('releves_notes.html', notes=notes)

# (Ajoute tes routes /ajouter_etudiant, /ajouter_note et /archives ici comme dans ton code)

if __name__ == '__main__':
    app.run(debug=True)