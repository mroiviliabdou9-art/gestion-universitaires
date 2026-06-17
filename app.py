import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'secret_2026'

def get_db():
    conn = sqlite3.connect('universite.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- ROUTES ---

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Vérification simplifiée (admin ou étudiant)
        id_user = request.form.get('identifiant')
        if id_user == 'admin': # Logique de connexion simplifiée
            session['user_id'] = 'admin'
            session['role'] = 'admin'
            return redirect(url_for('admin_panel'))
        # Sinon vérifie dans la table étudiants...
    return render_template('index.html')

@app.route('/admin')
def admin_panel():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    return render_template('Gestion_admin.html')

@app.route('/ajouter_etudiant', methods=['POST'])
def ajouter_etudiant():
    # Récupère tous les champs y compris le niveau/mention libre
    conn = get_db()
    conn.execute('INSERT INTO etudiants VALUES (?,?,?,?,?,?)', 
                 (request.form['id'], request.form['nom'], request.form['date_nais'], 
                  request.form['lieu'], request.form['mention'], request.form['mdp']))
    conn.commit()
    conn.close()
    flash("Étudiant ajouté !")
    return redirect(url_for('admin_panel'))

@app.route('/ajouter_note', methods=['POST'])
def ajouter_note():
    conn = get_db()
    conn.execute('INSERT INTO notes (id, matiere, note) VALUES (?,?,?)',
                 (request.form['id'], request.form['matiere'], request.form['note']))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/releve_notes')
def releve_notes():
    conn = get_db()
    # Calcule la moyenne et regroupe les notes
    notes = conn.execute('''SELECT matiere, GROUP_CONCAT(note, ', ') as liste_notes, 
                            AVG(note) as moyenne FROM notes WHERE id = ? 
                            GROUP BY matiere''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('releves_notes.html', notes=notes)

@app.route('/archives_etudiant')
def archives_etudiant():
    # Sécurité : accès admin seulement
    if session.get('role') != 'admin': return "Accès refusé", 403
    conn = get_db()
    archives = conn.execute('SELECT * FROM archives').fetchall()
    conn.close()
    return render_template('archives.html', archives=archives)

if __name__ == '__main__':
    app.run(debug=True)