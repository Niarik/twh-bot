import discord
import datetime
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
        "banner_url": "https://raw.githubusercontent.com/Niarik/twh-bot/main/theblooming.png",
        # Long, detailed narrative for #seasons channel
        "narrative": (
            "**The Blooming**\n\n"
            "The last of the snow has finally thawed; warm rain sweeps in and keeps water sources "
            "full to bursting and food sources plentiful. Chilly mornings and evenings are "
            "accompanied by thick fog; the weather varies from lengthy storms to brief showers. "
            "When the rain clears, it is cloudy and overcast, but the days are warm enough for "
            "most species to begin their first wave of nesting, hoping to raise their hatchlings "
            "enough to get them through the coming drought."
        ),
        # Short announcement for #announcements channel
        "announcement": (
            "🌸 **The Blooming has arrived** 🌸\n\n"
            "- Warm rains and storms\n"
            "- Thick fog in mornings and evenings\n"
            "- Food and water sources are abundant\n"
        ),
        "emoji": "🌸"
    },
    "The Drought": {
        "banner_url": "https://raw.githubusercontent.com/Niarik/twh-bot/main/thedrought.png",
        "narrative": (
            "**The Drought**\n\n"
            "The rains vanish and the heat scorches the land. Water sources dry up and only the "
            "strongest endure."
        ),
        "announcement": (
            "☀️ **The Drought has begun** ☀️\n\n"
            "- Clear, scorching skies\n"
            "- Water is scarce; travel to find survival"
        ),
        "emoji": "☀️"
    },
    "The Brightening": {
        "banner_url": "https://raw.githubusercontent.com/Niarik/twh-bot/main/thebrightening.png",
        "narrative": (
            "**The Brightening**\n\n"
            "The land recovers with light rain and warming sun. This is a season of balance "
            "and rebuilding."
        ),
        "announcement": (
            "🌤️ **The Brightening is here** 🌤️\n\n"
            "- Bright days with occasional rain\n"
            "- Nests resume, water and food begin to return"
        ),
        "emoji": "🌤️"
    },
    "The Freeze": {
        "banner_url": "https://raw.githubusercontent.com/Niarik/twh-bot/main/thefreeze.png",
        "narrative": (
            "**The Freeze**\n\n"
            "Snow blankets the land and bitter winds howl. Only the most prepared survive the cold."
        ),
        "announcement": (
            "❄️ **The Freeze has arrived** ❄️\n\n"
            "- Snow, fog and biting cold\n"
            "- Water sources freeze, food dwindles"
        ),
        "emoji": "❄️"
    }
}

class SeasonManager:
    def __init__(self, bot):
        self.bot = bot

    async def check_season_change(self):
        """
        Checks if 14 days have elapsed since last season start.
        If so, rotate to the next season.
        """
        last = get_last_season()
        now = datetime.datetime.utcnow()

        if last:
            start = datetime.datetime.fromisoformat(last["start"])
            if (now - start).days < SEASON_LENGTH_DAYS:
                # Not yet time to switch
                return

            last_index = SEASONS.index(last["season"])
            new_index = (last_index + 1) % len(SEASONS)
        else:
            # No previous season => start with The Blooming
            new_index = 0

        new_season = SEASONS[new_index]
        await self.apply_season_change(new_season, now)

    async def manual_set_season(self, season_name):
        """
        Force a season change from a slash command or direct call.
        """
        now = datetime.datetime.utcnow()
        if season_name not in SEASONS:
            raise ValueError("Unknown season.")
        await self.apply_season_change(season_name, now)

    async def apply_season_change(self, season_name, timestamp):
        """
        Applies the new season: updates #seasons channel and #announcements channel,
        changes the channel name, posts the banner + narrative, logs the event.
        """
        season_channel = self.bot.get_channel(CHANNEL_IDS["season"])
        announcements_channel = self.bot.get_channel(CHANNEL_IDS["announcements"])
        data = SEASON_DATA[season_name]

        # Clean old season posts in #seasons
        try:
            async for msg in season_channel.history(limit=5):
                if msg.author == self.bot.user:
                    await msg.delete()
        except Exception as e:
            print("Failed to clean season messages:", e)

        # Calculate timestamps
        start_ts = discord.utils.format_dt(timestamp, style='F')
        end_obj = timestamp + datetime.timedelta(days=SEASON_LENGTH_DAYS)
        end_ts = discord.utils.format_dt(end_obj, style='F')
        end_rel = discord.utils.format_dt(end_obj, style='R')

        # Update #seasons channel
        try:
            # 1) rename channel
            await season_channel.edit(name=f"{data['emoji']}season{data['emoji']}")
        except Exception as e:
            print("Failed to rename channel:", e)

        try:
            # 2) post banner
            await season_channel.send(data["banner_url"])

            # 3) post narrative
            narrative_msg = (
                f"{data['narrative']}\n\n"
                f"This season began {start_ts} and ends {end_ts} {end_rel}."
            )
            await season_channel.send(narrative_msg)

        except Exception as e:
            print("Failed to post banner/narrative:", e)

        # Announcements
        try:
            # 4) post simplified announcement embed
            embed = discord.Embed(
                description=data["announcement"],
                color=discord.Color.green()
            )
            ann_msg = await announcements_channel.send(embed=embed)

            # 5) publish the announcement if it's a news channel
            try:
                await ann_msg.publish()
            except Exception:
                pass  # probably not a news channel

        except Exception as e:
            print("Failed to post announcement:", e)

        # Save the new season info
        set_last_season({
            "season": season_name,
            "start": timestamp.isoformat()
        })

        # Log
        await log_to_discord(self.bot, f"Season changed to {season_name}")
