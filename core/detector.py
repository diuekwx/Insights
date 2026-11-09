from core.recorder import *
import time
import threading
from core.liveclient import get_data
from core.utils import check_process

# set by the stop button (on a different request thread); the loops in
# detection() and get_data() check it and wind down normally
stop_requested = threading.Event()


def request_stop():
    stop_requested.set()


def detection():
    stop_requested.clear()
    launch_obs()
    ws = websocket()
    while not check_process("League of Legends.exe"):
        if stop_requested.is_set():
            # stopped before a game started: nothing was recorded
            ws.disconnect()
            return None
        print("waiting")
        time.sleep(2)

    print("founds")
    record(ws)

    obs_start_time = time.time()

    # always stop OBS, even if polling crashes or stop is pressed
    try:
        timeline = get_data(obs_start_time, stop=stop_requested)
    finally:
        print("done")
        disconnect(ws)
    return timeline


