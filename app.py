import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'cle_secrete_universite_2026'

def get_db_connection():
    conn = sqlite3.connect('gestion_univ.db', timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Tables
    conn.execute('CREATE TABLE IF NOT EXISTS utilisateurs (id_utilisateur TEXT PRIMARY KEY, nom TEXT NOT NULL, mot_de_passe TEXT NOT NULL, role TEXT NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS ecolages (id_etudiant TEXT PRIMARY KEY, statut_paiement TEXT NOT NULL DEFAULT "Non payé", FOREIGN KEY (id_etudiant) REFERENCES utilisateurs (id_utilisateur))')
    conn.execute('CREATE TABLE IF NOT EXISTS notes (id_etudiant TEXT, matiere TEXT, note REAL, FOREIGN KEY (id_etudiant) REFERENCES utilisateurs (id_utilisateur))')
    
    # Admin par défaut
    admin = conn.execute('SELECT * FROM utilisateurs WHERE id_utilisateur = "ADM_01"').fetchone()
    if not admin:
        conn.execute('INSERT INTO utilisateurs VALUES ("ADM_01", "Admin", "admin123", "admin")', ())
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def se_connecter():
    if 'user_id' in session:
        return redirect(url_for('admin')) if session.get('role') == 'admin' else redirect(url_for('releve_notes'))

    if request.method == 'POST':
        user_id = request.form.get('identifiant', '').strip()
        password = request.form.get('password', '').strip()
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM utilisateurs WHERE id_utilisateur = ? AND mot_de_passe = ?', (user_id, password)).fetchone()
        conn.close()
        if user:
            session.update({'user_id': user['id_utilisateur'], 'nom': user['nom'], 'role': user['role']})
            return redirect(url_for('admin')) if user['role'] == 'admin' else redirect(url_for('releve_notes'))
        flash("Identifiant ou mot de passe incorrect.")
    return render_template('index.html')

@app.route('/admin')
def admin():
    if session.get('role') != 'admin': return redirect(url_for('se_connecter'))
    return render_template('Gestion_admin.html')

@app.route('/ajouter_etudiant', methods=['POST'])
def ajouter_etudiant():
    if session.get('role') != 'admin': return redirect(url_for('se_connecter'))
    id_et = request.form.get('id_etudiant', '').strip()
    nom = request.form.get('nom', '').strip()
    mdp = request.form.get('mot_de_passe', '').strip()
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO utilisateurs VALUES(?, ?, ?, "etudiant")', (id_et, nom, mdp))
        conn.execute('INSERT INTO ecolages (id_etudiant) VALUES(?)', (id_et,))
        conn.commit()
        flash("Étudiant inscrit avec succès !")
    except: flash("Erreur : Identifiant déjà utilisé.")
    conn.close()
    return redirect(url_for('admin'))

@app.route('/ajouter_note', methods=['POST'])
def ajouter_note():
    if session.get('role') != 'admin': return redirect(url_for('se_connecter'))
    id_et = request.form.get('id_etudiant', '').strip()
    mat = request.form.get('matiere', '').strip()
    note = request.form.get('note', '').strip()
    
    conn = get_db_connection()
    exists = conn.execute('SELECT * FROM utilisateurs WHERE id_utilisateur=?', (id_et,)).fetchone()
    if exists:
        conn.execute('INSERT INTO notes VALUES(?, ?, ?)', (id_et, mat, float(note)))
        conn.commit()
        flash("Note ajoutée !")
    else: flash("Étudiant introuvable.")
    conn.close()
    return redirect(url_for('admin'))

@app.route('/releve_notes')
def releve_notes():
    if 'user_id' not in session: return redirect(url_for('se_connecter'))
    conn = get_db_connection()
    # Vérification paiement
    paiement = conn.execute('SELECT statut_paiement FROM ecolages WHERE id_etudiant=?', (session['user_id'],)).fetchone()
    if paiement and paiement['statut_paiement'] == 'Non payé':
        conn.close()
        return "Accès restreint : Situation financière non réglée."
    
    mes_notes = conn.execute('SELECT matiere, note FROM notes WHERE id_etudiant=?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('releves_notes.html', notes=mes_notes)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('se_connecter'))

if __name__ == '__main__':
    app.run(debug=True)
