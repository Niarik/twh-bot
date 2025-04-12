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

# Weather flavour dictionary
WEATHER_FLAVOR = {
    "rain": [
        "🌧️ Rain begins to pelt the ground...",
        "🌧️ A gentle rain patters across the land...",
        "🌧️ A steady rain begins, soaking your scales..."
    ],
    "storm": [
        "⛈️ Thunder rumbles overhead...",
        "⛈️ The sky darkens as a storm brews overhead...",
        "⛈️ Lightning flickers in the distance, thunder roars..."
    ],
    "overcast": [
        "☁️ Dull grey clouds gather across the sky...",
        "☁️ The sky is thick with grey clouds...",
        "☁️ Grey clouds roll in..."
    ],
    "cloudy": [
        "🌤️ Gentle clouds drift across the sky...",
        "🌤️ The sun shines through fluffy white clouds..."
    ],
    "snow": [
        "❄️ Snowflakes begin to fall slowly to the ground...",
        "❄️ A thick flurry of snow sweeps in...",
        "❄️ Thick, heavy snowfall drifts down from the clouds..."
    ],
    "clearsky": [
        "☀️ The sun emerges, coating the world in warm light...",
        "☀️ The relentless sun scorches the ground...",
        "☀️ The earth is bathed in sunlight..."
    ],
    "fog": [
        "🌫️ A thick fog rolls in...",
        "🌫️ Mist rises, coating the world in white...",
        "🌫️ The world vanishes in thick white fog..."
    ]
}

class WeatherManager:
    def __init__(self, bot):
        self.bot = bot
        self.weather_interval = 20 * 60  # 20 minutes in seconds
        self.blooming_streak = 0
        self.last_rain_time = None

    async def start_weather_loop(self):
        """
        Repeats every 20 minutes. Checks pause state, picks new weather if unpaused.
        """
        while True:
            if not get_pause_state():
                await self.update_weather()
            await asyncio.sleep(self.weather_interval)

    async def update_weather(self):
        """
        Reads the current season, picks a random weather type (with constraints),
        sends an RCON command, and posts a flavor text message to #weather_updates.
        """
        season_info = get_last_season()
        if not season_info:
            # No season is set yet
            return

        season = season_info["season"]
        now = datetime.datetime.utcnow()
        possible_weathers = SEASON_WEATHER_RULES.get(season, [])
        if not possible_weathers:
            return

        chosen_weather = await self.pick_weather(season, possible_weathers, now)
        if chosen_weather:
            # Send RCON command to the server
            await send_rcon_command(f"/weather {chosen_weather}")
            set_last_weather(chosen_weather)

            # Select flavor text if available
            flavor_lines = WEATHER_FLAVOR.get(chosen_weather, [])
            if flavor_lines:
                flavor_text = random.choice(flavor_lines)
            else:
                flavor_text = f"The weather is now {chosen_weather}."

            # Post flavor text to weather_updates channel
            weather_channel = self.bot.get_channel(CHANNEL_IDS["weather_updates"])
            if weather_channel:
                await weather_channel.send(flavor_text)

            await log_to_discord(self.bot, f"[WeatherManager] Changed to '{chosen_weather}' - {flavor_text}")

    async def pick_weather(self, season, options, now):
        """
        Chooses weather based on:
          - Blooming: avoid 3 consecutive rain/storm
          - Brightening: only 1 rain every 6 hours with a 25% chance
          - Otherwise, random from the valid options
        """
        from storage import get_last_weather
        last_weather = get_last_weather()

        if season == "The Blooming":
            # If last weather was rain/storm, increment streak
            if last_weather in ("rain", "storm"):
                self.blooming_streak += 1
            else:
                self.blooming_streak = 0

            # If we've had 2 consecutive rain/storm, pick something else
            if self.blooming_streak >= 2:
                safe = [w for w in options if w not in ("rain", "storm")]
                if safe:
                    return random.choice(safe)

        elif season == "The Brightening":
            # If we rained <6 hours ago, remove 'rain' from the list
            if self.last_rain_time:
                six_hours_ago = now - datetime.timedelta(hours=6)
                if self.last_rain_time > six_hours_ago:
                    safe = [w for w in options if w != "rain"]
                    return random.choice(safe)

            # If we didn't remove 'rain', there's a 25% chance to choose it
            if "rain" in options and random.random() < 0.25:
                self.last_rain_time = now
                return "rain"
            else:
                # Otherwise exclude rain for this cycle
                safe = [w for w in options if w != "rain"]
                return random.choice(safe)

        # Default random pick
        return random.choice(options)
