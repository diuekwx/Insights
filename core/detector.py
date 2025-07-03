from core.recorder import record, websocket, disconnect
import time
from core.liveclient import get_data
from core.utils import check_process


# def all_processes():
#     for proc in psutil.process_iter(['name']):
#         print(proc.info['name'])

def detection():
    ws = websocket()
    while not check_process("League of Legends.exe"):
        print("waiting")
        time.sleep(2)

    print("founds")
    record(ws)

    obs_start_time = time.time()

    timeline = get_data(obs_start_time)

    print("done")
    disconnect(ws)
    return timeline


