import obsws_python as obs
import time
from .settings import OBS
import subprocess
import glob
import os
from core.utils import check_process

def compress_video(input_path, output_path, crf=28):
    # -y overwrites an existing output instead of asking on stdin, and stdin is
    # closed so ffmpeg can never sit waiting for an answer
    try:
        result = subprocess.run([
            'ffmpeg',
            '-y',
            '-i', input_path,
            '-vcodec', 'libx264',
            '-crf', str(crf),
            output_path
        ], stdin=subprocess.DEVNULL)
    except FileNotFoundError:
        print("ffmpeg not found on PATH, skipping compression")
        return
    if result.returncode != 0:
        print("ffmpeg failed with exit code", result.returncode)

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
    try:
        ws.stop_record()
        time.sleep(2)
        record_path =  get_path(ws)

        # list_of_files = glob.glob(os.path.join(record_path, '*.mp4'))
        # list_of_files.sort(key=os.path.getmtime)

        most_recent = retrieve_recent(record_path)

        # only change the extension, not every ".mp4" in the folder names
        compressed_path = os.path.splitext(most_recent)[0] + "_compressed.mp4"
        compress_video(most_recent, compressed_path)
    finally:
        # close the websocket even if finding/compressing the file fails
        ws.disconnect()

def record(ws):
    try:
        ws.set_current_program_scene("leaguegame")
        print("Scene set to leaguegame")
        ws.start_record()
        print("recording") 

    except (KeyboardInterrupt, Exception):
        # recording never started, so there is nothing to stop; just close
        # the connection and let the caller see the error
        ws.disconnect()
        raise
        