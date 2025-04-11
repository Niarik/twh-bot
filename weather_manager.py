import random
import datetime
import asyncio
from config import CHANNEL_IDS
from storage import (
    get_last_season, get_last_weather, set_last_weather,
    get_pause_state
)
from logger import log_to_discord
from rcon import send_rcon_command

SEASON_WEATHER_RULES = {
    "The Blooming": ["rain", "storm", "overcast", "cloudy", "fog"],
    "The Drought": ["clearsky"],
    "The Brightening": ["clearsky", "cloudy", "overcast", "rain"],
    "The Freeze": ["snow", "fog", "overcast", "cloudy"]
}

class WeatherManager:
    def __init__(self, bot):
        self.bot = bot
        self.weather_interval = 20 * 60  # 20 minutes
        self.blooming_streak = 0
        self.last_weather = get_last_weather()
        self.last_rain_time = None

    async def start_weather_loop(self):
        while True:
            if not get_pause_state():
                await self.update_weather()
            await asyncio.sleep(self.weather_interval)

    async def update_weather(self):
        season_data = get_last_season()
        if not season_data:
            return

        season = season_data["season"]
        now = datetime.datetime.utcnow()
        valid_weathers = SEASON_WEATHER_RULES.get(season, [])

        chosen_weather = await self.pick_weather(season, valid_weathers, now)

        if chosen_weather:
            await send_rcon_command(f"/weather {chosen_weather}")
            set_last_weather(chosen_weather)

            # Post update to Discord
            channel = self.bot.get_channel(CHANNEL_IDS["weather_updates"])
            if channel:
                await channel.send(f"**Weather Update:** `{chosen_weather}` now active.")

            await log_to_discord(self.bot, f"[Weather Manager] Changed weather to `{chosen_weather}`")

    async def pick_weather(self, season, options, now):
        last_weather = get_last_weather()

        if season == "The Blooming":
            # Prevent rain or storm 3 times in a row
            if last_weather in ["rain", "storm"]:
                self.blooming_streak += 1
            else:
                self.blooming_streak = 0

            if self.blooming_streak >= 2:
                non_repeatables = [w for w in options if w not in ["rain", "storm"]]
                return random.choice(non_repeatables)

        elif season == "The Brightening":
            # Allow rain only once every 6 hours
            if self.last_rain_time and (now - self.last_rain_time).total_seconds() < 6 * 3600:
                options = [w for w in options if w != "rain"]
            else:
                if random.random() < 0.25:
                    self.last_rain_time = now
                    return "rain"
                else:
                    options = [w for w in options if w != "rain"]

        return random.choice(options)
