#config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
RCON_HOST = os.getenv("RCON_HOST")
RCON_PORT = int(os.getenv("RCON_PORT"))
RCON_PASSWORD = os.getenv("RCON_PASSWORD")

CHANNEL_IDS = {
    "season": 1303375972258812036,
    "announcements": 1303378387947229225,
    "weather_updates": 1359519868168437790,
    "bot_logs": 1359506060414812284
}
