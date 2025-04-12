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
        "narrative": (
            "> The last of the snow has finally thawed, warm rain sweeps in and keeps water sources full to bursting and food sources plentiful. Chilly mornings and evenings are accompanied by thick fog, the weather varies from lengthy storms to brief showers. When the rain clears, it is cloudy and overcast, but the days are warm enough for most species to begin their first wave of nesting, hoping to raise their hatchlings enough to get them through the coming drought."
        ),
        "announcement": (
            "## 🌸 **The Blooming has arrived** 🌸\n\n"
            "> * Frequent rain and storms, mornings are chilly, daytimes are warm\n"
            "> * Food and water sources are abundant\n"
            "> * Most species are nesting\n"            
        ),
        "emoji": "🌸"
    },
    "The Drought": {
        "banner_url": "https://raw.githubusercontent.com/Niarik/twh-bot/main/thedrought.png",
        "narrative": (
            "> The drought is a true survival test for most species, as the rains disappear and the water sources dry up. Rare storms bring some relief, but most species will have to move often and venture outside of their territories to find enough water to survive. Hatchlings born in this season face enormous challenges and rarely make it to The Brightening."
        ),
        "announcement": (
            "## ☀️ **The Drought has begun** ☀️\n\n"
            "> * Water is scarce\n"
            "> * Wildfires possible\n"
            "> * Suffer quietly as you burn.\n"
        ),
        "emoji": "☀️"
    },
    "The Brightening": {
        "banner_url": "https://raw.githubusercontent.com/Niarik/twh-bot/main/thebrightening.png",
        "narrative": (
            "> The Brightening is the comfortably warm season following the drought. The weather is typically clear and bright, with periodic rains keeping water sources flowing and food plentiful. Many species will have a second wave of nests during this season, the last of the year. Towards the end of the season, most species will settle into territories they can stay in for The Freeze."
        ),
        "announcement": (
            "## 🌤️ **The Brightening is here** 🌤️\n\n"
            "> * The heat of the drought has eased but the weather remains clear\n"
            "> * Water sources have been replenished by periodic rains and the heat is not enough to deplete them\n"
            "> * The next wave of nesting has arrived for many species\n"
        ),
        "emoji": "🌤️"
    },
    "The Freeze": {
        "banner_url": "https://raw.githubusercontent.com/Niarik/twh-bot/main/thefreeze.png",
        "narrative": (
                "> During The Freeze, frosts are soon followed by thick snowfall, the temperature turns bitterly cold, many plants go dormant and water sources freeze over. Water is still accessible for large species who can break the ice, but some herds may have to periodically travel in search of roots and nuts. Carnivores are particularly dangerous during The Freeze, driven from their winter dens only by extreme hunger."
        ),
        "announcement": (
            "## ❄️ **The Freeze has arrived** ❄️\n\n"
            "> * The weather is cold, snowy and foggy\n"
            "> * Small water sources (excluding the Hot Springs) have frozen over completely but large water sources are kept flowing by large dinosaurs\n"
            "> * Freeze without complaint.\n"
        ),
        "emoji": "❄️"
    }
}

class SeasonManager:
    def __init__(self, bot):
        self.bot = bot

    async def check_season_change(self):
        """
        If no stored season or 14+ days have passed since last start,
        move to the next season. Otherwise do nothing.
        """
        last = get_last_season()
        now = datetime.datetime.utcnow()

        if last:
            start = datetime.datetime.fromisoformat(last["start"])
            if (now - start).days < SEASON_LENGTH_DAYS:
                # Not enough days have passed
                return

            # Rotate to next season in SEASONS list
            last_index = SEASONS.index(last["season"])
            new_index = (last_index + 1) % len(SEASONS)
        else:
            # If no previous season is saved, start at index 0
            new_index = 0

        new_season = SEASONS[new_index]
        await self.apply_season_change(new_season, now)

    async def manual_set_season(self, season_name):
        """
        Allows an admin to force the season via slash command or direct call.
        """
        now = datetime.datetime.utcnow()
        if season_name not in SEASONS:
            raise ValueError("Unknown season.")
        await self.apply_season_change(season_name, now)

    async def apply_season_change(self, season_name, timestamp):
        """
        Applies all season updates:
          1. Check if we've already posted this season recently
          2. Clean old bot messages in #season
          3. Post banner + narrative to #season
          4. Post short announcement in #announcements
          5. Rename channel with the new season emoji
          6. Save the new season to storage
          7. Log to #twh-bot-logs
        """
        season_channel = self.bot.get_channel(CHANNEL_IDS["season"])
        announcements = self.bot.get_channel(CHANNEL_IDS["announcements"])

        # Skip if we already posted this season
        if await self.check_already_posted(season_channel, season_name):
            print(f"Skipping re-post: the channel already has {season_name}.")
            return

        data = SEASON_DATA[season_name]

        # Clean up old season posts by our bot
        try:
            async for msg in season_channel.history(limit=5):
                if msg.author == self.bot.user:
                    await msg.delete()
        except Exception as e:
            print("Failed to clean season messages:", e)

        # Format timestamps
        start_ts = discord.utils.format_dt(timestamp, style='F')
        end_time = timestamp + datetime.timedelta(days=SEASON_LENGTH_DAYS)
        end_ts = discord.utils.format_dt(end_time, style='F')
        end_rel = discord.utils.format_dt(end_time, style='R')

        # Post banner + narrative
        await season_channel.send(data["banner_url"])
        narrative_msg = (
            f"{data['narrative']}\n\n"
            f"This season began {start_ts} and ends {end_ts} {end_rel}."
        )
        await season_channel.send(narrative_msg)

        # Short announcement embed
        embed = discord.Embed(
            description=data["announcement"],
            color=discord.Color.green()
        )
        ann_msg = await announcements.send(embed=embed)
        # Try to publish if it's a News channel
        try:
            await ann_msg.publish()
        except Exception:
            pass  # Not a News channel, ignore

        # Rename channel
        try:
            await season_channel.edit(name=f"{data['emoji']}season{data['emoji']}")
        except Exception as e:
            print("Failed to rename channel:", e)

        # Record the new season
        set_last_season({
            "season": season_name,
            "start": timestamp.isoformat()
        })

        await log_to_discord(self.bot, f"Season changed to {season_name}")

    async def check_already_posted(self, season_channel, season_name):
        """
        Checks the recent bot messages in #season 
        to see if there's already an announcement for this season.
        If we find a mention of the same season, we skip re-posting.
        """
        async for msg in season_channel.history(limit=5):
            if msg.author == self.bot.user:
                # Check if the message text references this season's name
                if season_name.lower() in msg.content.lower():
                    return True
        return False
