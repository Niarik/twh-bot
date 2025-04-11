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

# A dictionary mapping each season to possible weather types
SEASON_WEATHER_RULES = {
    "The Blooming": ["rain", "storm", "overcast", "cloudy", "fog"],
    "The Drought": ["clearsky"],
    "The Brightening": ["clearsky", "cloudy", "overcast", "rain"],
    "The Freeze": ["snow", "fog", "overcast", "cloudy"]
}

class WeatherManager:
    def __init__(self, bot):
        self.bot = bot
        self.weather_interval = 20 * 60  # 20 minutes in seconds
        self.blooming_streak = 0
        self.last_rain_time = None

    async def start_weather_loop(self):
        """
        This method runs continuously. Every 20 minutes, it checks if 
        weather updates are paused. If not, it picks new weather 
        and applies it via RCON.
        """
        while True:
            if not get_pause_state():
                await self.update_weather()
            await asyncio.sleep(self.weather_interval)

    async def update_weather(self):
        """
        Reads the current season from storage, picks a random weather type,
        and sends the /weather command via RCON.
        """
        season_data = get_last_season()
        if not season_data:
            return  # No season has been set yet

        season = season_data["season"]
        now = datetime.datetime.utcnow()

        # Get valid weather types for this season
        valid_options = SEASON_WEATHER_RULES.get(season, [])
        if not valid_options:
            return  # No valid weather for this season?

        chosen_weather = await self.pick_weather(season, valid_options, now)
        if chosen_weather:
            # Send RCON command
            await send_rcon_command(f"/weather {chosen_weather}")
            # Store the new weather so /seasoninfo can show it
            set_last_weather(chosen_weather)

            # Announce weather update in #weather_updates channel
            channel = self.bot.get_channel(CHANNEL_IDS["weather_updates"])
            if channel:
                await channel.send(f"**Weather Update:** `{chosen_weather}` now active.")
            await log_to_discord(self.bot, f"[WeatherManager] Changed weather to `{chosen_weather}`")

    async def pick_weather(self, season, options, now):
        """
        Returns a randomly chosen weather type, taking into account
        any special conditions such as:
          - The Blooming: no more than two consecutive rain/storm
          - The Brightening: only one rain every 6 hours
        """
        from storage import get_last_weather
        last_weather = get_last_weather() or ""

        if season == "The Blooming":
            # Avoid 3 consecutive rain/storm
            if last_weather in ["rain", "storm"]:
                self.blooming_streak += 1
            else:
                self.blooming_streak = 0

            if self.blooming_streak >= 2:
                # Exclude rain and storm from choices
                safe_options = [w for w in options if w not in ("rain", "storm")]
                if safe_options:
                    return random.choice(safe_options)
                # If somehow only rain/storm exist, fallback to full options

        elif season == "The Brightening":
            # Permit rain only once every 6 hours
            if self.last_rain_time:
                six_hours_ago = now - datetime.timedelta(hours=6)
                if self.last_rain_time > six_hours_ago:
                    # Exclude 'rain'
                    safe_options = [w for w in options if w != "rain"]
                    return random.choice(safe_options)

            # There's a 25% chance to pick rain
            # (You can adjust probability as you like)
            if "rain" in options and random.random() < 0.25:
                self.last_rain_time = now
                return "rain"
            else:
                # Exclude rain for this cycle
                safe_options = [w for w in options if w != "rain"]
                return random.choice(safe_options)

        # Default fallback: pick from all valid options
        return random.choice(options)
