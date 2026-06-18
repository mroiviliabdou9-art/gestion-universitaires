import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'projet_2k26_secret'
DB_PATH = os.path.join(os.path.dirname(__file__), 'universite.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # On supprime les anciennes tables pour éviter les conflits
    cursor.execute('DROP TABLE IF EXISTS etudiants')
    cursor.execute('DROP TABLE IF EXISTS notes')
    cursor.execute('DROP TABLE IF EXISTS admins')
    
    # On recrée tout proprement
    cursor.execute('''CREATE TABLE etudiants (id TEXT PRIMARY KEY, nom TEXT, mention TEXT, mdp TEXT)''')
    cursor.execute('''CREATE TABLE notes (id TEXT, matiere TEXT, note REAL, annee TEXT)''')
    cursor.execute('''CREATE TABLE admins (id TEXT PRIMARY KEY, password TEXT)''')
    
    # Insertion des 3 admins
    admins = [('admin1', '123'), ('admin2', '123'), ('admin3', '123')]
    cursor.executemany('INSERT INTO admins VALUES (?, ?)', admins)
    
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifiant = request.form.get('identifiant')
        password = request.form.get('password')
        
        conn = get_db()
        # Test Admin
        admin = conn.execute('SELECT * FROM admins WHERE id=? AND password=?', (identifiant, password)).fetchone()
        if admin:
            session['role'] = 'admin'
            return redirect(url_for('admin_panel'))
        
        # Test Étudiant
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