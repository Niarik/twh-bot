# weather_cycle.py
import random
import json
from discord.ext import tasks
from seasons import get_current_season, season_data
from datetime import datetime, timedelta
from mcrcon import MCRcon

bot_instance = None  # Will be set by main.py
weather_pause_until = None
recent_weather = []
MAX_RECENT = 6  # 6 x 20 minutes = 2 hours

def set_bot(bot):
    global bot_instance
    bot_instance = bot

def send_weather_command(weather_type, rcon_config):
    try:
        with MCRcon(rcon_config["host"], rcon_config["password"], port=rcon_config["port"]) as mcr:
            mcr.command(f"/weather {weather_type}")
            print(f"Sent weather command: {weather_type}")
    except Exception as e:
        print(f"RCON error: {e}")

@tasks.loop(minutes=20)
async def cycle_weather():
    global weather_pause_until

    if weather_pause_until and datetime.now() < weather_pause_until:
        print("Weather changes paused.")
        return

    with open("config.json", "r") as f:
        config = json.load(f)

    season = get_current_season()
    weather_options = season_data[season]["weather_options"]

    # Limit rain/storm during The Blooming
    if season == "the blooming":
        heavy_weather = [w for w in recent_weather if w in ["rain", "storm"]]
        if heavy_weather.count("rain") >= 2:
            weather_options = [w for w in weather_options if w != "rain"]
        if heavy_weather.count("storm") >= 2:
            weather_options = [w for w in weather_options if w != "storm"]

    weather = random.choice(weather_options)
    send_weather_command(weather, config["rcon"])

    if bot_instance:
        channel = bot_instance.get_channel(config["announce_channel_id"])
        if channel:
            descriptions = {
                "snow": "❄️ The skies darken as snow begins to fall...",
                "fog": "🌫️ A thick fog rolls across the land...",
                "overcast": "☁️ The sky turns a dull grey as clouds gather...",
                "rain": "🌧️ Rain begins to patter against the ground...",
                "clearsky": "☀️ The clouds part and the sun shines brightly.",
                "storm": "🌩️ Thunder rumbles as a storm brews overhead...",
                "cloudy": "⛅ Light clouds drift lazily across the sky."
            }
            await channel.send(descriptions.get(weather, f"Weather changed to: {weather}"))

    recent_weather.append(weather)
    if len(recent_weather) > MAX_RECENT:
        recent_weather.pop(0)

def pause_weather_for(hours):
    global weather_pause_until
    weather_pause_until = datetime.now() + timedelta(hours=hours)

def resume_weather():
    global weather_pause_until
    weather_pause_until = None