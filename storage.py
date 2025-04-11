#storage.py
import json

STORAGE_FILE = "data.json"

def load_data():
    try:
        with open(STORAGE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(STORAGE_FILE, "w") as f:
        json.dump(data, f, indent=4)


def get_last_season():
    return load_data().get("last_season")

def set_last_season(season_info):
    data = load_data()
    data["last_season"] = season_info
    save_data(data)


def get_last_weather():
    return load_data().get("last_weather")

def set_last_weather(weather):
    data = load_data()
    data["last_weather"] = weather
    save_data(data)


def get_pause_state():
    return load_data().get("pause_weather", False)

def set_pause_state(paused):
    data = load_data()
    data["pause_weather"] = paused
    save_data(data)
