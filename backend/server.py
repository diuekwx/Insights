import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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

timeline = None
is_recording = False

@app.route("/start-recording")
def start_or_stop_recording():
    global timeline, is_recording
    try:
        recording = request.args.get("recording", "false").lower() == "true"
        print("recording", recording)
        if recording:
            # Flask serves requests on separate threads, so a second click
            # would start a second recorder alongside the first
            if is_recording:
                return jsonify({"text": "Already recording"})
            print("Starting recording...")
            is_recording = True
            timeline = None
            try:
                timeline = detection()
            finally:
                is_recording = False
        else:
            print("Stopping early...")
            is_recording = False
            disconnect()
        
        # an empty list (game with no kills) is still a timeline
        return jsonify(timeline if timeline is not None else {"status": "Recording stopped. No timeline available."})
    
    except Exception as e:
        return jsonify({"text": "Error starting/stopping recording", "error": str(e)})

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
    try:
        path = get_path(ws)
        recent_path = retrieve_recent(path)
    finally:
        # each call opened a new OBS connection and never closed it
        ws.disconnect()

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
    app.run(port=5000, debug=False, use_reloader = False)