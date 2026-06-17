import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'cle_secrete_universite_2026'

DB_FILE = 'gestion_univ.db' 
def get_db_connection():
    conn = sqlite3.connect('gestion_univ.db',timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # Création des tables si elles n'existent pas
    conn.execute('''
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id_utilisateur TEXT PRIMARY KEY,
            nom TEXT NOT NULL,
            mot_de_passe TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ecolages (
            id_etudiant TEXT PRIMARY KEY,
            statut_paiement TEXT NOT NULL DEFAULT 'Non payé',
            FOREIGN KEY (id_etudiant) REFERENCES utilisateurs (id_utilisateur)
        )
    ''')
    
    # Insertion automatique de ton compte admin si la base est vide
    conn.execute('''
        INSERT OR IGNORE INTO utilisateurs (id_utilisateur, nom, mot_de_passe, role)
        VALUES ('ADM_01', 'Administrateur Principal', 'admin123', 'admin')
    ''')
    
    conn.commit()
    conn.close()

# Initialisation automatique au démarrage
init_db()

@app.route('/', methods=['GET', 'POST'])
def se_connecter():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('releve_notes'))

    if request.method == 'POST':
        user_id = request.form.get('Identifiant', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM utilisateurs WHERE id_utilisateur = ? AND mot_de_passe = ?', (user_id, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id_utilisateur']
            session['nom'] = user['nom']
            session['role'] = user['role']

            if user['role'] == 'admin':
                return redirect(url_for('admin'))
            elif user['role'] == 'etudiant':
                conn = get_db_connection()
                ecolage = conn.execute('SELECT statut_paiement FROM ecolages WHERE id_etudiant = ?', (user_id,)).fetchone()
                conn.close()

                if ecolage and ecolage['statut_paiement'] == 'Non payé':
                    flash("🔒 Accès refusé : Votre situation financière n'est pas en règle.")
                    session.clear()
                    return redirect(url_for('se_connecter'))
                
                return redirect(url_for('releve_notes'))
        else:
            flash("Identifiant ou mot de passe incorrect.")
            return redirect(url_for('se_connecter'))

    return render_template('index.html')

@app.route('/admin')
def admin():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('se_connecter'))
    return render_template('Gestion_admin.html')
  

    # 1- Enregistrement des etudiant et ecolage
@app.route('/ajouter_etudiant', methods=['POST'])
def ajouter_etudiant():
    if'user_id' not in session or session.get('role')!='admin':
        return redirect(url_for(se_connecter))

    id_etudiant= request.form.get('id_etudiant','').strip()
    nom_etudiant= request.form.get('nom','').strip()
    mot_de_passe_etudiant= request.form.get('mot_de_passe','')
    statut_paiement= request.form.get('statut_paiement','Nom paye').strip()

    if id_etudiant and nom_etudiant and mot_de_passe_etudiant:
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO utilisateurs VALUES(?, ?, ?, "etudiant")',(id_etudiant,nom_etudiant,mot_de_passe_etudiant))
            conn.execute('INSERT INTO ecolages VALUES(?, ?)',(id_etudiant,statut_paiement))
            conn.commit()
            flash(f"L'Etudiant{nom_etudiant} a ete inscrit avec succes!")
        except sqlite3.IntegrityError:
            flash("Erreur: Cet identifiant etudiant existe deja.")
        finally:
            conn.close()
    else:
        flash("Veuillez remplire tous les cases.")
        return redirect(url_for('admin'))

 # 2- Enregistrement des notes
@app.route('/ajouter_note', methods=['POST'])
def ajouter_note():
    if'user_id' not in session or session.get('role')!='admin':
        return redirect(url_for('se_connecter'))

    id_etudiant= request.form.get('id_etudiant','').strip()
    matiere= request.form.get('matiere','').strip()
    valeur_note= request.form.get('note','').strip()
    if id_etudiant and matiere and valeur_note:
        conn=get_db_connection()
        etudiant_existe= conn.execute('SELECT* FROM utilisateurs WHERE id_utilisateur=? AND role="etudiant"',(id_etudiant,)).fetchone()

        if etudiant_existe:
           conn.execute('INSERT INTO notes (id_etudiant,matiere,note) VALUES(?, ?, ?)',(id_etudiant,matiere,float(valeur_note)))
           conn.commit()
           flash(f"Note de{valeur_note} ajouter en {matiere} pour l'etudiant {id_etudiant}!")
        else:
            flash("Erreur: Cet identifiant n'appartient a aucun etudiant inscrit.")
            conn.close()
    else:
        flash("Veuillez remplire tous les cases de la note.")
    return redirect(url_for('admin'))        

# Fonctinnalite 3&4- Modification du profil et acces
@app.route('/modifier_profil', methods=['POST'])
def modifier_profil():
  if'user_id' not in session:
    return redirect(url_for(se_connecter))
    ancien_mot_de_passe= request.form.get('ancien_mot_de_passe','').strip()
    nouveau_mot_de_passe= request.form.get('nouveau_mot_de_passe','').strip()
    conn= get_db_connection
    user = conn.execute('SELECT*FROM utilisateur WHERE id_utilisateur=?',(session['user_id'],)).fetchone()

    if user and user['mot_de_passe'] == ancien_mot_de_passe:
        conn.execute('UPDATE utilisateur SET mot_de_passe=? WHERE id_utilisateur=?',(nouveau_mot_de_passe,session['user_id']))
        conn.commit()
        flash("votre mot de passe a bien ete modifier!")
    else:
        flash("L'ancien mot de passe est incorrect.")
        conn.close()
    return redirect(url_for('admin') if session['role'] =='admin' else url_for('releve_notes'))

# 3- Affichage du releve d notes
@app.route('/releve_notes')
def releve_notes():
    if'user_id'not in session or session.get('role')!='etudiant':
        return redirect(url_for(se_connecter))

    conn= get_db_connection
    etudiant= conn.execute('SELECT paiement FROM utilisateurs WHERE id_utilisateur=?', (session['user_id'],)).fetchone()
    if etudiant and etudiant['paiement']=='non_paye':
        conn.close()
        return render_template('Releves_notes.html', restriction=True, notes=[])
    mes_notes= conn.execute('SELECT matiere, note FROM notes WHERE id_etudiant=?',(session['user_id'],)).fetchall()
    conn.close()
    return render_template('Releves_notes.html',notes=mes_notes)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('se_connecter'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

