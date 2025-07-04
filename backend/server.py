from flask import Flask, request, jsonify
from core.recorder import *
from core.detector import *
from core.riot import *
from core.liveclient import *

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, World!"


@app.route("/hello")
def get_text():
    return jsonify({"text": "Text from Flask Backend!"})

@app.route("/start-recording")
def start():
    try:
        print("recording!")
        timeline = detection()
        # returns timeline once the recording is finished 
        return jsonify(timeline)
    
    except:
        return jsonify({"text": "Error starting recording"})

@app.route("/stop-recording")
def stop():
    try:
        disconnect()
    except:
        return jsonify({"text": "No recording detected"})
    

@app.route("/get-video")
def video():
    # get video after disconnect -> should return the compressed video
    ws = websocket()
    path = get_path(ws)
    recent_path = retrieve_recent(path)
    
    return jsonify(recent_path)


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
    app.run(port=5000, debug=True)