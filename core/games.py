import json
import os
import time

# one JSON file per finished game: {"id", "video", "events", "finished_at"}.
# a file only appears once its game is completely saved (video stopped and
# compressed), so "the newest file" is always a game the page can show
GAMES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "games")


def save_game(video_path, events):
    os.makedirs(GAMES_DIR, exist_ok=True)
    finished_at = time.time()
    # sortable by name: the newest game is the last file in sorted order
    game_id = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(finished_at))
    path = os.path.join(GAMES_DIR, game_id + ".json")
    game = {"id": game_id, "video": video_path, "events": events, "finished_at": finished_at}

    # write under a temporary name, then rename: the rename is atomic, so a
    # reader never sees a half-written file
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(game, f, indent=2)
    os.replace(tmp_path, path)
    return game_id


def latest_game_id():
    try:
        names = os.listdir(GAMES_DIR)
    except FileNotFoundError:
        return None
    ids = sorted(name[:-len(".json")] for name in names if name.endswith(".json"))
    return ids[-1] if ids else None


def load_game(game_id):
    with open(os.path.join(GAMES_DIR, game_id + ".json"), encoding="utf-8") as f:
        return json.load(f)
