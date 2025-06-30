from flask import Flask, request, jsonify
from core.recorder import *
from core.detector import *

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
        detection()
    
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



if __name__ == '__main__':
    app.run(port=5000, debug=True)