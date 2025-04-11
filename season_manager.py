#season_manager.py
import discord
import datetime
from discord.utils import escape_markdown
from config import CHANNEL_IDS
from storage import get_last_season, set_last_season
from logger import log_to_discord

SEASON_LENGTH_DAYS = 14

SEASONS = [
    "The Blooming",
    "The Drought",
    "The Brightening",
    "The Freeze"
]

SEASON_DATA = {
    "The Blooming": {
        "banner_url": "https://github.com/Niarik/twh-bot/blob/main/theblooming.png",
        "narrative": "The last of the snow has finally thawed, warm rain sweeps in and keeps water sources full to bursting and food sources plentiful. Chilly mornings and evenings are accompanied by thick fog, the weather varies from lengthy storms to brief showers. When the rain clears, it is cloudy and overcast, but the days are warm enough for most species to begin their first wave of nesting, hoping to raise their hatchlings enough to get them through the coming drought.",
    },
    "The Drought": {
        "banner_url": "https://github.com/Niarik/twh-bot/blob/main/thedrought.png",
        "narrative": "The drought is a true survival test for most species, as the rains disappear and the water sources dry up. Rare storms bring some relief, but most species will have to move often and venture outside of their territories to find enough water to survive. Hatchlings born in this season face enormous challenges and rarely make it to The Brightening.",
    },
    "The Brightening": {
        "banner_url": "https://github.com/Niarik/twh-bot/blob/main/thebrightening.png",
        "narrative": "The Brightening is the comfortably warm season following the drought. The weather is typically clear and bright, with periodic rains keeping water sources flowing and food plentiful. Many species will have a second wave of nests during this season, the last of the year. Towards the end of the season, most species will settle into territories they can stay in for The Freeze.",
    },
    "The Freeze": {
        "banner_url": "https://github.com/Niarik/twh-bot/blob/main/thefreeze.png",
        "narrative": "During The Freeze, frosts are soon followed by thick snowfall, the temperature turns bitterly cold, many plants go dormant and water sources freeze over. Water is still accessible for large species who can break the ice, but some herds may have to periodically travel in search of roots and nuts. Carnivores are particularly dangerous during The Freeze, driven from their winter dens only by extreme hunger.",
    }
}

class SeasonManager:
    def __init__(self, bot):
        self.bot = bot

    async def check_season_change(self):
        last = get_last_season()
        now = datetime.datetime.utcnow()

        if last:
            start = datetime.datetime.fromisoformat(last["start"])
            days_elapsed = (now - start).days
            if days_elapsed < SEASON_LENGTH_DAYS:
                print("Season has not changed yet.")
                return

            last_index = SEASONS.index(last["season"])
            new_index = (last_index + 1) % len(SEASONS)
        else:
            new_index = 0  # first season

        new_season = SEASONS[new_index]
        await self.apply_season_change(new_season, now)

    async def manual_set_season(self, season_name):
        now = datetime.datetime.utcnow()
        if season_name not in SEASONS:
            raise ValueError("Unknown season.")
        await self.apply_season_change(season_name, now)

    async def apply_season_change(self, season_name, timestamp):
        channel = self.bot.get_channel(CHANNEL_IDS["season"])
        announcements = self.bot.get_channel(CHANNEL_IDS["announcements"])

        # Delete previous 2 season posts
        try:
            async for msg in channel.history(limit=5):
                if msg.author == self.bot.user:
                    await msg.delete()
        except Exception as e:
            print("Error cleaning up old season messages:", e)

        # Post banner
        banner_url = SEASON_DATA[season_name]["banner_url"]
        await channel.send(banner_url)

        # Format Discord timestamps
        start_ts = discord.utils.format_dt(timestamp, style='F')
        end_ts_obj = timestamp + datetime.timedelta(days=SEASON_LENGTH_DAYS)
        end_ts = discord.utils.format_dt(end_ts_obj, style='F')
        end_relative = discord.utils.format_dt(end_ts_obj, style='R')

        # Post narrative
        narrative = SEASON_DATA[season_name]["narrative"]
        narrative_msg = f"**{season_name}**\n\n{narrative}\n\nThis season started {start_ts}, it will end {end_ts} {end_relative}."
        await channel.send(narrative_msg)

        # Post summary to announcements
        summary = f"**Season Change: {season_name}**\n{narrative}"
        announcement = await announcements.send(summary)
        try:
            await announcement.publish()
        except Exception:
            pass  # Not a news channel? Skip.

        # Edit season channel name
        try:
            await channel.edit(name=f"🌸season🌸")
        except Exception as e:
            print("Failed to edit channel name:", e)

        # Store new season data
        set_last_season({
            "season": season_name,
            "start": timestamp.isoformat()
        })

        await log_to_discord(self.bot, f"Season changed to {season_name}")
