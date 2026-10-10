from flask_cors import CORS
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, decode_token
from supabase import create_client
from flask_socketio import SocketIO, join_room, leave_room, emit
import logging
from games.petit_bac import belongTo
from datetime import timedelta
import bcrypt
import uuid
import random
import threading
from tiktok import get_stream_url, transcribe_live, isLivingDef
from datetime import datetime
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s -%(message)s"
)

app = Flask(__name__)

# Activer CORS pour toutes les routes et pour toutes les origines
CORS(app, resources={r"/*": {"origins": "*"}})

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")


DATABASE_URL = "https://zkxdazowhbkgvbzmtfbm.supabase.co"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpreGRhem93aGJrZ3Ziem10ZmJtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTU5OTg3NSwiZXhwIjoyMDg3MTc1ODc1fQ.fluUKxT5uBNJWA2sLF5UA8zQkSacpAQ3YE5ntm6_Uw0"

Supabase = create_client(DATABASE_URL, API_KEY)

games = {}
app.config['JWT_SECRET_KEY'] = 'super-secret-key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=15)

jwt = JWTManager(app)

categories = ["prenomsF", "prenomsM", "metiers", "legumesfruits", "paysvilles", "celebrities"]

@app.post('/login')
def login():
    data = request.get_json()
    identifiant = data.get('identifiant')
    password = data.get('password')

    #app.cur.execute(f"SELECT * FROM public.\"Users\" WHERE identifiant='{identifiant}'")
    response = (
        Supabase.table("Users")
        .select("*")
        .eq("name", identifiant)
        .execute()
    )
    users = response.data
    logging.info("response")
    logging.info(response.data)

    if (len(users) != 0):
        logging.info(users[0]["password"].encode("utf-8"))
        logging.info(password.encode("utf-8"))
        if bcrypt.checkpw(password.encode("utf-8"), users[0]["password"].encode("utf-8")) :
            token = create_access_token(identity=identifiant)
            return jsonify(access_token=token, time_token=users[0]["time_token"]), 200
    return jsonify(msg="Invalid credentials"), 401

@app.get('/profile')
@jwt_required()
def profile():
    current_user = get_jwt_identity()
    return jsonify(user=current_user), 200

@app.post('/signIn')
def signIn():
    data = request.get_json()
    identifiant = data.get('identifiant')
    password = data.get('password')

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()) 
    hashed_str = hashed.decode("utf-8") # store this in DB

    print(hashed_str)
    (
        Supabase.table("Users")
        .insert({"name" : identifiant, "password": hashed_str})
        .execute()
    )
    return "OK", 200


@app.route('/getTiktokLive/<string:user_id>')
def getTiktokLive(user_id):
    """ print(user_id)
    maintenant = datetime.now().strftime("%d%m%Y_%H%M")
    print(maintenant)
    dossier = "./resume/" + user_id + "/" + maintenant
    os.makedirs(dossier, exist_ok=True) """
    url = get_stream_url(user_id)
    """ thread = threading.Thread(target=transcribe_live, args=(url, "./resume/" + user_id + "/" + maintenant + "/retranscription.txt"), daemon=True)
    thread.start() """
    return url, 200

@app.route('/isLiving/<string:user_id>')
async def isLiving(user_id):
    print(user_id)
    result = await isLivingDef(user_id)
    print(result)
    return str(result), 200

@socketio.on("check_on")
def get_data(data):
    room = data["room"]
    valeur = data["valeur"]
    categorie = data["categorie"]
    res = belongTo(valeur, categorie)
    if res:
        games[room]["players"][request.sid]["ans"][categorie] = [valeur, "Good"]
        print(f"{valeur} appartient bien à {categorie}")
    else:
        games[room]["players"][request.sid]["ans"][categorie] = [valeur, "Bad"]
        print(f"{valeur} n'appartient pas à {categorie}")
    emit("check_receive", {"res": res, "categorie": categorie}, room=room, to=request.sid)

@socketio.on("connect")
def handle_connect(auth):
    try:
        decoded = decode_token(auth["token"])
        user_id = decoded["sub"]  # équivalent de get_jwt_identity()

        print("Utilisateur connecté :", user_id)

        # tu peux stocker l'user dans la session socket
        request.environ["user_id"] = user_id

    except Exception as e:
        print("JWT invalide :", e)
        return False

@socketio.on("create_game")
def create_game():
    room_id = str(uuid.uuid4())[:6]

    games[room_id] = {
        "players": {},
        "round": 0,
        "started": False,
        "stopped": False,
        "letter": None,
        "letters": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
    }

    emit("game_created", {"room": room_id})

@socketio.on("send_message")
def send_message(data):
    print("message reçu:", data["message"])
    emit("receive_message", {"message": data["message"]}, room=data["room"], include_self=False)
        

@socketio.on("join_game")
def join_game(data):
    room = data["room"]

    name = request.environ["user_id"]

    print(name)
    print(room)
    print(games)

    if room not in games:
        emit("error", {"message": "Partie introuvable"})
        return

    join_room(room)
    print(request.sid)

    if request.sid not in games[room]["players"]:
        games[room]["players"][request.sid] = {
            "name": name,
            "ready": "Bad",
            "score": 0,
            "ans": {
                "prenomsF": ["No Answer", "Bad"],
                "prenomsM": ["No Answer", "Bad"],
                "metiers": ["No Answer", "Bad"],
                "legumesfruits": ["No Answer", "Bad"],
                "paysvilles": ["No Answer", "Bad"],
                "celebrities": ["No Answer", "Bad"]
            }
        }

    emit("players_update", list_players(room), room=room)

@socketio.on("player_ready")
def player_ready(data):
    print(data)
    room = data["room"]
    games[room]["players"][request.sid]["ready"] = "Good"

    emit("players_update", list_players(room), room=room)

    if all(p["ready"] == "Good" for p in games[room]["players"].values()) and len(games[room]["players"]) == 4 and games[room]["round"]<26:        start_round(room)

@socketio.on("scoreFinal")
def score_final(data):
    room = data["room"]
    list_sid = [sid for sid in games[room]["players"]]
    result = []
    for sid in list_sid:
        result.append({games[room]["players"][sid]["name"]: [games[room]["players"][sid]["score"], "Good"]})
    emit("end_game", {"score": result}, room=room)

@socketio.on("stop_game")
def stop_game(data):
    room = data["room"]

    if games[room]["stopped"]:
        return

    games[room]["stopped"] = True
    
    for play in games[room]["players"]:
        games[room]["players"][play]["ready"] = "Bad"

    list_sid = [sid for sid in games[room]["players"]]
    players = games[room]["players"]

    result = []
    for cat in categories:
        result_cat = {}
        answers = []
        for sid in list_sid:
            answers.append(players[sid]["ans"][cat][0])
        print("list answers : ", answers)
        for sid in list_sid:
            classAns = ""
            if answers.count(players[sid]["ans"][cat][0]) >= 2 and players[sid]["ans"][cat][0] != "No Answer":
                print(f"{sid} a eu une réponse similaire")
                classAns = "Draw"
                players[sid]["score"] += 1
            else:
                classAns = players[sid]["ans"][cat][1]
                if players[sid]["ans"][cat][1] == "Good":
                    players[sid]["score"] += 2
            result_cat[players[sid]["name"]] = [players[sid]["ans"][cat][0], classAns]
        result.append(result_cat)
        

    emit("players_update", list_players(room), room=room)
    emit("game_stopped", {"message": "STOP !"}, room=room, include_self=False)
    emit("end_round", {"ans": result}, room=room)

@socketio.on("disconnect")
def disconnect():
    for room, game in games.items():
        if request.sid in game["players"]:
            del game["players"][request.sid]
            emit("players_update", list_players(room), room=room)
            break


def start_round(room):
    letter_ind = random.randint(1, len(games[room]["letters"]))
    print(letter_ind)
    letter = games[room]["letters"].pop(letter_ind-1)
    print(games[room]["letters"])

    games[room]["round"] += 1
    games[room]["started"] = True
    games[room]["stopped"] = False
    games[room]["letter"] = letter

    emit("round_started", {"letter": letter}, room=room)

def list_players(room):
    return [
        {
            "name": p["name"],
            "ready": p["ready"],
            "score": p["score"]
        }
        for p in games[room]["players"].values()
    ]

import time
import requests

BASE_URL = "https://www.dnd5eapi.co/api/2014"
OUTPUT_FILE = "spells_fr.json"

session = requests.Session()
session.headers.update({
    "Accept": "application/json",
    "User-Agent": "JDR-Site/1.0"
})


def get_json(url, params=None):
    response = session.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def get_all_spells():
    """
    Récupère la liste de tous les sorts.
    """
    print("Récupération de la liste des sorts...")

    data = get_json(f"{BASE_URL}/spells")

    return data["results"]


def get_spell_details(spell_index):
    """
    Récupère les détails d'un sort en français.
    """
    url = f"{BASE_URL}/spells/{spell_index}"

    # lang=fr-FR demande la traduction française
    return get_json(url, params={"lang": "fr-FR"})


def fetchingSpells():
    spells = get_all_spells()

    print(f"{len(spells)} sorts trouvés.\n")

    all_spells = []

    for i, spell in enumerate(spells, start=1):
        index = spell["index"]

        print(f"[{i}/{len(spells)}] {spell['name']}...", end=" ")

        try:
            details = get_spell_details(index)
            print(details)
            desc = ""
            deschl = ""
            if len(details["desc"]) > 0:
                desc = details["desc"][0]
            if len(details["higher_level"]) > 0:
                deschl = details["higher_level"][0]
            response = (
                    Supabase.table("Sort_JDR")
                    .insert({
                        "niveau": details["level"],
                        "portee": details["range"],
                        "composantes": details["components"],
                        "duree": details["duration"],
                        "description": desc,
                        "description_haut_niveau": deschl,
                        "classes": ",".join([classe["name"] for classe in details["classes"]])
                    })
                    .execute()
                )
            
            all_spells.append(details)

            print("OK")

        except requests.RequestException as e:
            print(f"ERREUR : {e}")

        # Petite pause pour éviter d'envoyer trop de requêtes
        time.sleep(0.05)

    print(f"\nTerminé !")
    print(f"{len(all_spells)} sorts sauvegardés dans {OUTPUT_FILE}")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)