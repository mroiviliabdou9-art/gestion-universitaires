import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'projet_2k26_secret'
DB_PATH = os.path.join(os.path.dirname(__file__), 'universite.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS etudiants (id TEXT PRIMARY KEY, nom TEXT, mention TEXT, mdp TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS notes (id TEXT, matiere TEXT, note REAL, semestre TEXT, annee TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS admins (id TEXT PRIMARY KEY, password TEXT)''') 
    cursor.execute('''CREATE TABLE IF NOT EXISTS configuration (periode_active TEXT, expiration_time TIMESTAMP)''')
    
    cursor.execute("SELECT count(*) FROM admins")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('INSERT INTO admins VALUES (?, ?)', [('admin1', '123'), ('admin2', '123')])
    
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
    res = conn.execute('SELECT periode_active FROM configuration LIMIT 1').fetchone()
    conn.close()
    return res['periode_active'] if res else "FERME"

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # .strip() élimine les espaces accidentels au début/fin
        identifiant = request.form.get('identifiant', '').strip()
        password = request.form.get('password', '').strip()
        
        conn = get_db()
        # Test Admin
        admin = conn.execute('SELECT * FROM admins WHERE id=? AND password=?', (identifiant, password)).fetchone()
        if admin:
            session['role'] = 'admin'
            conn.close()
            return redirect(url_for('admin_panel'))
            
        # Test Étudiant
        print(f"DEBUG - Tentative avec ID: '{identifiant}' et MDP: '{password}'")
        etu = conn.execute('SELECT * FROM etudiants WHERE id=? AND mdp=?', (identifiant, password)).fetchone()
        conn.close()
        
        if etu:
            session['role'] = 'etudiant'
            session['user_id'] = identifiant
            return redirect(url_for('releve_notes'))
        else:
            return "Identifiant ou mot de passe incorrect.", 401
            
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
                     (request.form.get('id').strip(), request.form.get('nom'), request.form.get('mention'), request.form.get('mdp')))
        conn.commit()
    except Exception as e: return f"Erreur lors de l'inscription : {e}", 500
    finally: conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/ajouter_note', methods=['POST'])
def ajouter_note():
    if session.get('role') != 'admin': return "Accès refusé", 403
    
    mat_etu = request.form.get('id', '').strip()
    matiere = request.form.get('matiere')
    note = request.form.get('note')
    semestre = request.form.get('semestre')
    annee = request.form.get('annee', '').strip()
    
    try:
        note_val = float(note)
    except: return "Erreur : La note doit être un nombre.", 400

    conn = get_db()
    try:
        etudiant = conn.execute('SELECT 1 FROM etudiants WHERE id = ?', (mat_etu,)).fetchone()
        if not etudiant: return f"Erreur : Étudiant {mat_etu} inconnu.", 404

        conn.execute('INSERT INTO notes (id, matiere, note, semestre, annee) VALUES (?, ?, ?, ?, ?)', 
                     (mat_etu, matiere, note_val, semestre, annee))
        conn.commit()
    finally: conn.close()
    return redirect(url_for('admin_panel'))


@app.route('/releve_notes')
def releve_notes():
    if 'user_id' not in session: 
        return redirect(url_for('login'))
    
    conn = get_db()
    
    # 1. Vérification de la configuration (accès et date)
    config = conn.execute('SELECT * FROM configuration LIMIT 1').fetchone()
    
    now = datetime.datetime.now()
    expiration = None
    if config and config['expiration_time']:
        try:
            expiration = datetime.datetime.fromisoformat(config['expiration_time'])
        except ValueError:
            expiration = None
            
    if not config or config['periode_active'] == "FERME" or (expiration and now > expiration):
        conn.close()
        return "L'accès est actuellement fermé ou le délai est expiré.", 403
    
    periode_active = config['periode_active']

    # 2. Récupération des notes pour la période active uniquement
    # On filtre par ID et par la période (S1, S2, REPECHAGE)
    toutes_les_notes = conn.execute(
        'SELECT * FROM notes WHERE id = ? AND semestre = ?', 
        (session['user_id'], periode_active)
    ).fetchall()
    
    # 3. Récupération des infos étudiant
    etudiant = conn.execute('SELECT * FROM etudiants WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()

    # 4. Calcul des moyennes par matière
    releve_calcule = {}
    for n in toutes_les_notes:
        mat = n['matiere']
        if mat not in releve_calcule:
            releve_calcule[mat] = {'notes': [], 'matiere': mat}
        releve_calcule[mat]['notes'].append(float(n['note']))

    for mat in releve_calcule:
        liste = releve_calcule[mat]['notes']
        releve_calcule[mat]['liste_notes'] = ", ".join(map(str, liste))
        releve_calcule[mat]['moyenne'] = sum(liste) / len(liste)

    # 5. Affichage
    return render_template(
        'releves_notes.html', 
        notes=releve_calcule.values(), 
        etudiant=etudiant, 
        periode=periode_active,
        est_admin=False
    )


@app.route('/update_periode', methods=['POST'])
def update_periode():
    if session.get('role') != 'admin': return "Accès refusé", 403
    
    periode = request.form.get('periode')
    delai_minutes = int(request.form.get('delai')) # Nouveau champ dans ton HTML
    
    # Calcul de l'heure d'expiration
    expiration = datetime.datetime.now() + datetime.timedelta(minutes=delai_minutes)
    
    conn = get_db()
    conn.execute('UPDATE configuration SET periode_active = ?, expiration_time = ?', 
                 (periode, expiration))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_panel'))

@app.route('/archives', methods=['POST'])
def archives():
    if session.get('role') != 'admin': return "Accès refusé", 403
    
    mat_etu = request.form.get('id', '').strip()
    annee = request.form.get('annee', '').strip()
    
    conn = get_db()
    # 1. Récupération des données brutes
    notes_brutes = conn.execute(
        'SELECT * FROM notes WHERE id = ? AND annee = ?', 
        (mat_etu, annee)
    ).fetchall()
    
    etudiant = conn.execute('SELECT * FROM etudiants WHERE id = ?', (mat_etu,)).fetchone()
    conn.close()
    
    if not notes_brutes:
        return f"Aucune note trouvée pour le matricule {mat_etu} en {annee}.", 404
    
    # 2. Calcul des moyennes (pour que le template fonctionne)
    releve_calcule = {}
    for n in notes_brutes:
        mat = n['matiere']
        if mat not in releve_calcule:
            releve_calcule[mat] = {'notes': [], 'matiere': mat}
        releve_calcule[mat]['notes'].append(float(n['note']))

    for mat in releve_calcule:
        liste = releve_calcule[mat]['notes']
        releve_calcule[mat]['liste_notes'] = ", ".join(map(str, liste))
        releve_calcule[mat]['moyenne'] = sum(liste) / len(liste)
    
    # 3. Affichage en passant les mêmes variables que dans releve_notes
    return render_template(
        'releves_notes.html', 
        notes=releve_calcule.values(), 
        etudiant=etudiant, 
        periode=f"Archive Année {annee}",
        est_admin=True
    )

if __name__ == '__main__':
    app.run(debug=True)