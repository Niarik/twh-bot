import random
import datetime
import asyncio
from config import CHANNEL_IDS
from storage import (
    get_last_season, get_last_weather, set_last_weather,
    get_pause_state
)
from logger import log_to_discord
from rcon import send_rcon_command  # You need to define this

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
        self.last_rain_time = None
        self.blooming_streak = 0

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
        weather_options = SEASON_WEATHER_RULES.get(season, [])

        # Blooming restriction
        if season == "The Blooming":
            prev = get_last_weather()
            if prev in ["rain", "storm"]:
                self.blooming_streak += 1
            else:
                self.blooming_streak = 0

            if self.blooming_streak >= 2:
                weather_options = [w for w in weather_options if w not in ["rain", "storm"]]

        # Brightening rain control
        if season == "The Brightening":
            if self.last_rain_time:
                time_since_rain = (now - self.last_rain_time).total_seconds()
                if time_since_rain < 6 * 3600:
                    weather_options = [w for w in weather_options if w != "rain"]
            else:
                self.last_rain_time = now  # init fallback

        chosen_weather = random.choice(weather_options)
        set_last_weather(chosen_weather)

        if season == "The Brightening" and chosen_weather == "rain":
            self.last_rain_time = now

        await send_rcon_command(f"/weather {chosen_weather}")

        # Post to Discord
        channel = self.bot.get_channel(CHANNEL_IDS["weather_updates"])
        if channel:
            await channel.send(f"**Weather Update:** `{chosen_weather}` set for **{season}**.")
        await log_to_discord(self.bot, f"Weather changed to {chosen_weather}")
