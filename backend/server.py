import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import threading
from flask import Flask, jsonify
from core.riot import *
from core.liveclient import *
from core.detector import watch, get_status
from core.games import latest_game_id, load_game

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, World!"


@app.route("/hello")
def get_text():
    return jsonify({"text": "Text from Flask Backend!"})

# recording is automatic: the watcher thread started below records every
# game, and the page polls these two routes to show what it is doing

@app.route("/status")
def watcher_status():
    # "latest" is the id of the newest saved game; it changes when one is saved
    return jsonify({**get_status(), "latest": latest_game_id()})


@app.route("/latest-game")
def latest_game():
    game_id = latest_game_id()
    if game_id is None:
        return jsonify({"text": "No games recorded yet"}), 404
    return jsonify(load_game(game_id))


@app.route("/game-stats")
def status():
    timeline = get_timeline("NA1_5317559791")
    print(timeline)
    kills = champ_kills(timeline)
    print(kills)
    timestamp = []
    for kill in kills:
        timestamp.append(kill[0])
    
    return jsonify(timestamp)

if __name__ == '__main__':
    # daemon: the thread never keeps the process alive on its own
    threading.Thread(target=watch, daemon=True).start()
    app.run(port=5000, debug=False, use_reloader = False)