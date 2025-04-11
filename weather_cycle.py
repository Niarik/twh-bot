import random
from discord.ext import tasks
from datetime import datetime, timedelta
import asyncio
import os
import json
from seasons import get_current_season, get_current_season_times
from mcrcon import MCRcon

current_weather = None
bot_reference = None
paused_until = None

SEASON_WEATHER = {
    "The Blooming": ["rain", "cloudy", "storm", "fog", "overcast"],
    "The Drought": ["clearsky", "cloudy"],
    "The Brightening": ["clearsky", "cloudy", "overcast"],
    "The Freeze": ["snow", "fog", "overcast"]
}

SEASON_WATER_RULES = {
    "The Drought": {"set": 0, "partial": 40},
    "The Freeze": {"set": 0, "partial": 100},
    "The Brightening": {"set": 100},
    "The Blooming": {"set": None}  # no changes
}

IMPORTANT_WATER_LOCATIONS = [
    "TriadFalls", "WhistlingLake", "TitansPassLake", "BigQuillLake",
    "HuntersThicket", "GreenValley", "WhiteCliffsLake", "RockfallHill"
] + [f"Hotspring{i}" for i in range(1, 25)]

with open("config.json", "r") as f:
    config = json.load(f)

@tasks.loop(minutes=config["interval_minutes"])
async def cycle_weather():
    global current_weather

    if paused_until and datetime.utcnow() < paused_until:
        return

    season = get_current_season()
    weather_choices = SEASON_WEATHER.get(season, ["clearsky"])

    if season == "The Blooming" and current_weather in ["rain", "storm"]:
        weather_choices = [w for w in weather_choices if w not in ["rain", "storm"]]

    chosen_weather = random.choice(weather_choices)
    current_weather = chosen_weather

    with MCRcon(
        os.getenv("RCON_HOST"),
        os.getenv("RCON_PASSWORD"),
        port=int(os.getenv("RCON_PORT"))
    ) as mcr:
        mcr.command(f"/weather {chosen_weather}")
        print(f"[Weather Update] {chosen_weather}")

@tasks.loop(hours=3)
async def update_water_quality():
    season = get_current_season()
    rules = SEASON_WATER_RULES.get(season)

    if not rules:
        print("No water update needed for this season.")
        return

    with MCRcon(
        os.getenv("RCON_HOST"),
        os.getenv("RCON_PASSWORD"),
        port=int(os.getenv("RCON_PORT"))
    ) as mcr:
        for location in IMPORTANT_WATER_LOCATIONS:
            if "partial" in rules:
                value = rules["partial"]
            else:
                value = rules["set"]
            if value is not None:
                mcr.command(f"/waterquality {location} {value}")
        print(f"[Water Quality] Updated for season {season}")

# Update these variables wherever your weather logic runs
def get_weather_info():
    global current_weather, last_weather_change
    return current_weather, last_weather_change

# Pausing logic
def pause_weather_for(hours):
    global paused_until
    paused_until = datetime.utcnow() + timedelta(hours=hours)
    print(f"Weather updates paused until {paused_until}")

def resume_weather():
    global paused_until
    paused_until = None
    print("Weather updates resumed")

def set_bot(bot):
    global bot_reference
    bot_reference = bot

def start_season_schedule():
    cycle_weather.start()
    update_water_quality.start()
