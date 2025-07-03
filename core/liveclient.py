import base64
import requests
import urllib3
import os
import time
from core.utils import check_process
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# league client api 
def lockfile():
    lockfile_path = r"C:\Riot Games\League of Legends\lockfile"
    if not os.path.exists(lockfile_path):
        raise RuntimeError("client not found")
    
    with open(lockfile_path, "r") as f:
        content = f.read()
    
    stuff = content.split(":")
    port = stuff[2]
    pw = stuff[3]
    return port, pw

def get_summoner():
    url = "https://127.0.0.1:2999/liveclientdata/activeplayername"
    try:
        res = requests.get(url, verify=False)
        return res.json()
    except Exception as e:
        print("Summoner not found")

def offsetCalculation():
    return time.time 

print(time.perf_counter())

#live client api
# probably have to use live eventdata because of recording offset//dont know how fast updated
def get_data(obs_start_time, poll_interval=1):
    url = "https://127.0.0.1:2999/liveclientdata/eventdata"
    game_events = []
    seen_ids = set()
    offset = None

    print("Started polling live events...")

    while True:
        try:
            res = requests.get(url, verify=False)
            if res.status_code == 200:
                data = res.json()
                events = data["Events"]

                for event in events:
                    event_id = event.get("EventID")
                    if event_id in seen_ids:
                        continue
                    seen_ids.add(event_id)

                    name = event["EventName"]

                    if name == "GameStart":
                        offset = time.time() - obs_start_time
                        print(f"GameStart detected. Offset = {offset:.2f}s")

                    elif name == "ChampionKill":
                        vod_time = time.time() - obs_start_time
                        print(f"[{vod_time:.2f}s] Kill: {event['KillerName']} → {event['VictimName']}")
                        game_events.append({
                            "type": "kill",
                            "killer": event["KillerName"],
                            "victim": event["VictimName"],
                            "vod_time": vod_time,
                            "kills": 1
                        })

                    elif name == "Multikill":
                        vod_time = time.time() - obs_start_time
                        print(f"[{vod_time:.2f}s] Multikill: {event['KillerName']} x{event['KillStreak']}")
                        game_events.append({
                            "type": "multikill",
                            "killer": event["KillerName"],
                            "vod_time": vod_time,
                            "kills": event["KillStreak"]
                        })

        except Exception as e:
            print("Error polling:", e)

        if not check_process("League of Legends.exe"):
            print("Game has ended.")
            break

        time.sleep(poll_interval)

    return game_events
