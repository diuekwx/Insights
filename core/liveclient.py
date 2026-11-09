import base64
import requests
import urllib3
import os
import time
from core.utils import *
from core.riot import *
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

#returns full id with tag
def get_summoner():
    url = "https://127.0.0.1:2999/liveclientdata/activeplayername"
    try:
        res = requests.get(url, verify=False, timeout=5)
        return res.json()
    except Exception as e:
        print("Summoner not found")

#current game clock in seconds
def game_time():
    url = "https://127.0.0.1:2999/liveclientdata/gamestats"
    res = requests.get(url, verify=False, timeout=5)
    return res.json()["gameTime"]

def player_list():
    url = "https://127.0.0.1:2999/liveclientdata/playerlist"
    players = []
    try:
        res = requests.get(url, verify=False, timeout=5)
        data = res.json()
        for player in data:
            players.append(player["riotId"])

    except:
        print("shit dont work")
    return players

def active_summoners_kills():
    # Riot IDs are "name#tag"; names can contain spaces
    summ = get_summoner().split("#")
    ppuid = get_summoner_by_name("americas", summ[0], summ[1])["puuid"]
    # match ids come newest first
    match = most_recent_match(ppuid)[0]
    timeline = get_timeline(match)
    kills = champ_kills(timeline)
    player_kills = []
    for kill in kills:
        if kill[1] == get_summoner():
            player_kills.append(kill)
    return player_kills


#live client api
# probably have to use live eventdata because of recording offset//dont know how fast updated
# stop: optional threading.Event; when set, polling ends early
def get_data(obs_start_time, poll_interval=1, stop=None):
    url = "https://127.0.0.1:2999/liveclientdata/eventdata"
    game_events = []
    seen_ids = set()
    offset = None

    # the game process starts at the loading screen, before this API answers,
    # so wait until it returns the player's name (a string)
    summoner = get_summoner()
    while not isinstance(summoner, str):
        if not check_process("League of Legends.exe") or (stop and stop.is_set()):
            return game_events
        time.sleep(poll_interval)
        summoner = get_summoner()
    summoner_name = summoner.split("#")[0]

    print("Started polling live events...")

    while True:
        try:
            res = requests.get(url, verify=False, timeout=5)
            if res.status_code == 200:
                data = res.json()
                events = data["Events"]

                # offset = seconds into the recording when the game clock was 0.
                # anchored to the current game time so it is also right when
                # polling starts mid-game (old events arrive all at once then)
                if offset is None:
                    current = game_time()
                    # a clock still at 0 (loading screen) can't anchor anything yet
                    if current > 0:
                        offset = (time.time() - obs_start_time) - current
                        print(f"Offset = {offset:.2f}s")
                if offset is None:
                    # leave events unseen; they are read again on the next poll
                    events = []

                for event in events:
                    event_id = event.get("EventID")
                    if event_id in seen_ids:
                        continue
                    seen_ids.add(event_id)

                    name = event["EventName"]
                    #consider case where they start recording in middle of game
                    #make sure gamestart -> never little offset
                    if name == "GameStart":
                        print("GameStart detected.")

                    elif name == "ChampionKill" and event["KillerName"] == summoner_name:
                        vod_time = offset + event["EventTime"]
                        print(f"[{vod_time:.2f}s] Kill: {event['KillerName']} → {event['VictimName']}")
                        game_events.append({
                            "type": "kill",
                            "killer": event["KillerName"],
                            "victim": event["VictimName"],
                            "vod_time": vod_time,
                            "real_time": event["EventTime"],
                            "kills": 1
                        })

                    elif name == "Multikill" and event["KillerName"] == summoner_name:
                        vod_time = offset + event["EventTime"]
                        print(f"[{vod_time:.2f}s] Multikill: {event['KillerName']} x{event['KillStreak']}")
                        game_events.append({
                            "type": "multikill",
                            "killer": event["KillerName"],
                            "vod_time": vod_time,
                            "real_time": event["EventTime"],
                            "kills": event["KillStreak"]
                        })
        # end of game leads to exception 
        except Exception as e:
            print("Error polling:", e)

        if not check_process("League of Legends.exe"):
            print("Game has ended.")
            break
        if stop and stop.is_set():
            print("Stopped early.")
            break

        time.sleep(poll_interval)

    return game_events

def active_player_data(gameEvents):
    activeSummonerKills = active_summoners_kills()
    playerEvents = []
    for event in gameEvents:
        for kills in activeSummonerKills:
            if event["real_time"] == kills[0]:
                playerEvents.append(event)
    return playerEvents

