import obsws_python as obs
import time
from .settings import OBS
import subprocess
import glob
import os
from core.utils import check_process

def compress_video(input_path, output_path, crf=28):
    subprocess.run([
        'ffmpeg',
        '-i', input_path,
        '-vcodec', 'libx264',
        '-crf', str(crf),
        output_path
    ])

def launch_obs():
    obs_path = "C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe"
    obs_dir = os.path.dirname(obs_path)
    running = check_process("obs64.exe")
    if not running: 
        print("obs opened")
        subprocess.Popen([
            obs_path,
            "--minimize-to-tray"
        ], 
        cwd=obs_dir)
    time.sleep(5)

def websocket():
    ws = obs.ReqClient(host="localhost", port=4455, password=OBS)
    return ws

def get_path(ws):
    return ws.get_record_directory().record_directory

def retrieve_recent(path):
    list_of_files = glob.glob(os.path.join(path, '*.mp4'))
    list_of_files.sort(key=os.path.getmtime)
    
    return list_of_files[-1]

# delete video


def disconnect(ws):
    ws.stop_record()
    time.sleep(2)
    record_path =  get_path(ws)
    
    # list_of_files = glob.glob(os.path.join(record_path, '*.mp4'))
    # list_of_files.sort(key=os.path.getmtime)
    
    most_recent = retrieve_recent(record_path)

    compressed_path = most_recent.replace(".mp4", "_compressed.mp4")
    compress_video(most_recent, compressed_path)
    ws.disconnect()

def record(ws):
    try:
        ws.set_current_program_scene("leaguegame")
        print("Scene set to leaguegame")
        ws.start_record()
        print("recording") 

    except KeyboardInterrupt or Exception:
        disconnect(ws)
        