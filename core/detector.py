import time
from core.recorder import launch_obs, websocket, record, disconnect
from core.liveclient import get_data
from core.utils import check_process
from core.games import save_game

# the game itself (not the launcher/lobby): it exists from the loading screen
# until the game window closes
GAME_PROCESS = "League of Legends.exe"
CHECK_INTERVAL = 2  # seconds between process checks

# what the watcher is doing, for /status:
#   watching   no game running
#   recording  a game is running and OBS records it
#   saving     the game closed; stopping OBS, compressing, saving the kill list
#   error      recording this game failed (shown until the game closes)
_status = {"state": "watching", "detail": None}


def get_status():
    return _status


def _set_status(state, detail=None):
    global _status
    # replace the dict instead of editing it, so a request thread reading it
    # never sees a half-updated status
    _status = {"state": state, "detail": detail}


def game_running():
    return check_process(GAME_PROCESS)


def record_game():
    """Record the game that is running now; returns the saved game's id."""
    _set_status("recording", "Starting OBS")
    launch_obs()
    ws = websocket()
    record(ws)
    obs_start_time = time.time()
    _set_status("recording")

    # always stop OBS, even if polling crashes
    try:
        events = get_data(obs_start_time)
    finally:
        _set_status("saving")
        video_path = disconnect(ws)
    return save_game(video_path, events)


def watch():
    """Runs in a background thread for as long as the server does and
    records every game that starts."""
    last_error = None
    while True:
        _set_status("watching", last_error)
        while not game_running():
            time.sleep(CHECK_INTERVAL)

        print("Game found, recording it")
        try:
            print("Saved game", record_game())
            last_error = None
        except Exception as e:
            print("Recording failed:", e)
            last_error = f"Last recording failed: {e}"
            _set_status("error", str(e))

        # record each game once: after a failure the game is still running,
        # so wait for it to close instead of retrying every few seconds
        while game_running():
            time.sleep(CHECK_INTERVAL)
