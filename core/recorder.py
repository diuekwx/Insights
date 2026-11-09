import obsws_python as obs
import time
from .settings import OBS
import subprocess
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
        return False
    if result.returncode != 0:
        print("ffmpeg failed with exit code", result.returncode)
        return False
    return True

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
        # give OBS a head start loading its scenes; websocket() below keeps
        # retrying until its server answers
        time.sleep(5)

def websocket(timeout=30):
    # a freshly started OBS takes a few seconds to open its websocket server,
    # so retry instead of failing the whole recording on the first refusal
    deadline = time.time() + timeout
    while True:
        try:
            return obs.ReqClient(host="localhost", port=4455, password=OBS)
        except Exception as e:
            if time.time() >= deadline:
                raise
            print("OBS not ready yet:", e)
            time.sleep(2)

def get_path(ws):
    return ws.get_record_directory().record_directory

def wait_until_stopped(ws, timeout=60):
    # stop_record returns before OBS has finished writing the file
    deadline = time.time() + timeout
    while ws.get_record_status().output_active and time.time() < deadline:
        time.sleep(0.5)

# delete video


# stops OBS and returns the path of the finished video: the compressed copy,
# or the original recording if compression failed
def disconnect(ws):
    try:
        # OBS reports the file it wrote (any format: mp4, mkv, ...), so there
        # is no need to guess the newest file in the folder
        recording = ws.stop_record().output_path
        wait_until_stopped(ws)

        # only change the extension, not every ".mp4" in the folder names
        compressed_path = os.path.splitext(recording)[0] + "_compressed.mp4"
        if compress_video(recording, compressed_path):
            return compressed_path
        return recording
    finally:
        # close the websocket even if compressing the file fails
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
        