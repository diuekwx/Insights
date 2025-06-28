import obsws_python as obs
import sys
import time 
from settings import OBS


def websocket():
    ws = obs.ReqClient(host="localhost", port=4455, password=OBS)

def record(ws):
    try:
        ws.set_current_program_scene("leaguegame")
        print("Scene set to leaguegame")
        ws.start_record()
        print("recording") 
        

    except KeyboardInterrupt:
        pass


def disconnect(ws):
    ws.stop_record()
    ws.disconnect()
