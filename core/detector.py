from core.recorder import *
import time
from core.liveclient import get_data
from core.utils import check_process


def detection():
    launch_obs()
    ws = websocket()
    while not check_process("League of Legends.exe"):
        print("waiting")
        time.sleep(2)

    print("founds")
    record(ws)

    obs_start_time = time.time()

    # always stop OBS, even if polling crashes
    try:
        timeline = get_data(obs_start_time)
    finally:
        print("done")
        disconnect(ws)
    return timeline


