import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'projet_2k26_secret'

def get_db():
    conn = sqlite3.connect('universite.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- CONNEXION UNIQUE ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifiant = request.form.get('identifiant')
        password = request.form.get('password')
        
        if identifiant == 'admin' and password == 'admin':
            session['role'] = 'admin'
            return redirect(url_for('admin_panel'))
        
        conn = get_db()
        etu = conn.execute('SELECT * FROM etudiants WHERE id=? AND mdp=?', (identifiant, password)).fetchone()
        conn.close()
        
        if etu:
            session['role'] = 'etudiant'
            session['user_id'] = identifiant
            return redirect(url_for('releve_notes'))
            
    return render_template('index.html')

# --- ADMINISTRATION ---
@app.route('/admin')
def admin_panel():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    return render_template('Gestion_admin.html')

@app.route('/ajouter_etudiant', methods=['POST'])
def ajouter_etudiant():
    conn = get_db()
    conn.execute('INSERT INTO etudiants (id, nom, mention, mdp) VALUES (?,?,?,?)', 
                 (request.form['id'], request.form['nom'], request.form['mention'], request.form['mdp']))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/ajouter_note', methods=['POST'])
def ajouter_note():
    conn = get_db()
    conn.execute('INSERT INTO notes (id, matiere, note) VALUES (?,?,?)', 
                 (request.form['id'], request.form['matiere'], request.form['note']))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

# --- RELEVÉ ÉTUDIANT ---
@app.route('/releve_notes')
def releve_notes():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    notes = conn.execute('''SELECT matiere, GROUP_CONCAT(note, ', ') as liste_notes, 
                            AVG(note) as moyenne FROM notes WHERE id = ? 
                            GROUP BY matiere''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('releves_notes.html', notes=notes)

# --- ARCHIVES (Admin seulement) ---
@app.route('/archives', methods=['GET', 'POST'])
def archives():
    if session.get('role') != 'admin': return "Accès refusé", 403
    resultats = []
    if request.method == 'POST':
        id_etu = request.form.get('id')
        annee = request.form.get('annee')
        conn = get_db()
        resultats = conn.execute('SELECT * FROM notes WHERE id=? AND annee=?', (id_etu, annee)).fetchall()
        conn.close()
    return render_template('archives.html', notes=resultats)

if __name__ == '__main__':
    app.run(debug=True)