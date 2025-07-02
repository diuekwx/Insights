import base64
import requests
import urllib3
import os
import time

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

#live client api
# probably have to use live eventdata because of recording offset//dont know how fast updated
def get_data(poll_interval=1):
    url = "https://127.0.0.1:2999/liveclientdata/eventdata"
    eventIds = {}
    summoner = get_summoner()
    while True:
        try:
            res = requests.get(url, verify=False)
            if res.status_code == 200:
                data = res.json()
                events = data["Events"]
                game_events = []
                for event in events:
                    if event["EventID"] not in eventIds:
                        eventIds.add(event["EventID"])

                        if event["EventName"] == "GameStart":
                            startTime = event["EventTime"] 
                            # offset = startTime - 2 
                            # check assisters 
                        elif event["EventName"] == "ChampionKill":
                            game_events.append({
                                "type": "kill",
                                "killer": event["KillerName"],
                                "victim": event["VictimName"],
                                "vod_time": event["EventTime"],
                                "kills": 1
                            })
                        elif event["EventName"] == "Multikill":
                                game_events.append({
                                "type": "multikill",
                                "killer": event["KillerName"],
                                "victim": event["VictimName"],
                                "vod_time": event["EventTime"],
                                "kills": event["KillStreak"]
                            })
                        
                
        except Exception as e:
            pass
        time.sleep(poll_interval)

get_data()