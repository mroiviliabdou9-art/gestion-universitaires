import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client

app = Flask(__name__)
app.secret_key = 'projet_2k26_secret'


# On récupère les clés depuis les "Variables d'environnement" du serveur
load_dotenv('cle.env')
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifiant = request.form.get('identifiant', '').strip()
        password = request.form.get('password', '').strip()
        
        # Test Admin
        admin = supabase.table('admins').select("*").eq('id', identifiant).eq('password', password).execute()
        if admin.data:
            session['role'] = 'admin'
            return redirect(url_for('admin_panel'))
            
        # Test Étudiant
        etu = supabase.table('etudiants').select("*").eq('id', identifiant).eq('mdp', password).execute()
        if etu.data:
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

# Route pour ajouter une note (Admin)
@app.route('/ajouter_note', methods=['POST'])
def ajouter_note():
    if session.get('role') != 'admin': return "Accès refusé", 403
    
    try:
        data = {
            "etudiant_id": request.form.get('id', '').strip(),
            "matiere": request.form.get('matiere'),
            "note": float(request.form.get('note')),
            "semestre": request.form.get('semestre'),
            "annee": request.form.get('annee', '').strip()
        }
        # Insertion dans la table 'notes'
        supabase.table('notes').insert(data).execute()
        return redirect(url_for('admin_panel'))
    except ValueError:
        return "Erreur : La note doit être un nombre valide.", 400
    except Exception as e:
        return f"Une erreur est survenue : {str(e)}", 500

# Route pour voir les notes (Étudiant)
@app.route('/releve_notes')
def releve_notes():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # 1. Vérification de la période
    config = supabase.table('configuration').select("*").limit(1).execute().data[0]
    if not config or config['periode_active'] == "FERME":
        return "L'accès est actuellement fermé.", 403

    periode = config['periode_active']
    
    # 2. Récupération des notes avec le bon nom de colonne : 'etudiant_id'
    notes_data = supabase.table('notes') \
        .select("*") \
        .eq('etudiant_id', session['user_id']) \
        .eq('semestre', periode) \
        .execute().data

    # 3. Calcul des moyennes
    releve_calcule = {}
    for n in notes_data:
        mat = n['matiere']
        if mat not in releve_calcule: releve_calcule[mat] = {'notes': [], 'matiere': mat}
        releve_calcule[mat]['notes'].append(float(n['note']))

    for mat in releve_calcule:
        liste = releve_calcule[mat]['notes']
        releve_calcule[mat]['moyenne'] = round(sum(liste) / len(liste), 2)

    return render_template('releves_notes.html', notes=releve_calcule.values(), periode=periode)
@app.route('/update_periode', methods=['POST'])
def update_periode():
    if session.get('role') != 'admin': 
        return "Accès refusé", 403
    
    # On récupère la valeur envoyée par le formulaire
    nouvelle_valeur = request.form.get('periode')
    
    # On met à jour directement la ligne de configuration (en supposant qu'elle a l'id 1)
    # Si ta table n'a pas de colonne 'id', utilise la colonne qui identifie ta ligne unique
    supabase.table('configurations').update({"periode_active": nouvelle_valeur}).eq('id', 1).execute()
    
    return redirect(url_for('admin_panel'))
@app.route('/archive', methods=['GET', 'POST'])
def archive():
    if session.get('role') != 'admin': return "Accès refusé", 403
    
    notes = None
    if request.method == 'POST':
        etu_id = request.form.get('id', '').strip()
        annee = request.form.get('annee', '').strip()
        
        # Récupération des notes selon les critères
        notes = supabase.table('notes') \
            .select("*") \
            .eq('etudiant_id', etu_id) \
            .eq('annee', annee) \
            .execute().data
            
    return render_template('archive.html', notes=notes)

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/update_profil', methods=['POST'])
def update_profil():
    if session.get('role') != 'admin': return "Accès refusé", 403
    
    new_user = request.form.get('new_username')
    new_pass = request.form.get('new_password')
    
    # Mise à jour dans Supabase (dans la table 'admins')
    # On met à jour l'admin actuellement connecté
    supabase.table('admins').update({
        'id': new_user,
        'password': new_pass
    }).eq('id', session.get('user_id')).execute()
    
    return "Profil mis à jour ! <a href='/admin'>Retour</a>"
