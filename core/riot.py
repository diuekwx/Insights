import requests
from settings import RIOT_API

API_KEY = RIOT_API
SUMMONER_NAME = "goodbye yeri"
TAG_LINE = "1229"
REGION = "americas"


def get_summoner_by_name(region, gameName, tagLine):
    url = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"
    headers = {"X-Riot-Token": API_KEY}
    res = requests.get(url, headers=headers)
    return res.json()

def get_summoner_by_puuid(region, puuid):
    url = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}"
    headers = {"X-Riot-Token": API_KEY}
    res = requests.get(url, headers=headers)
    return (res.json()["gameName"] + "#" + res.json()["tagLine"])


# print(get_summoner_by_name(REGION, SUMMONER_NAME, TAG_LINE))
data = get_summoner_by_name(REGION, SUMMONER_NAME, TAG_LINE)
print("PUUID:", data["puuid"])


def most_recent_match(puuid):
    url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
    headers = {"X-Riot-Token": API_KEY}
    res = requests.get(url,headers=headers)
    return res.json()

recent = most_recent_match(data["puuid"])[0]
print(most_recent_match(data["puuid"])[0])

def get_timeline(matchId):
    url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{matchId}/timeline"
    headers = {"X-Riot-Token": API_KEY}
    res = requests.get(url,headers=headers)
    return res.json()

def participants(match_timeline):
    participants = match_timeline["info"]["participants"]
    players = {}
    for participant in participants:
        id = participant['participantId']
        puuid = participant['puuid']
        name = get_summoner_by_puuid("americas", puuid)
        players[id] = name
    return players

timeline = get_timeline(recent)
# print(participants(timeline))

def champ_kills(match_timeline):
    events = match_timeline["info"].get("frames")
    players = participants(match_timeline)
    kill_list = []
    for frame in events:
        for event in frame["events"]:
            if event["type"] == "CHAMPION_KILL":
                timestamp = event["timestamp"] // 1000
                kill_list.append((timestamp, players[event["killerId"]], players[event["victimId"]]))

    return kill_list



# print(champ_kills(timeline))
# print(get_timeline(recent))
