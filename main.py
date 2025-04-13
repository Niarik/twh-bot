import asyncio
import discord
from discord.ext import commands
from discord import Intents
from config import BOT_TOKEN
from config import GUILD_ID
from season_manager import SeasonManager
from weather_manager import WeatherManager
from water_manager import WaterManager
from webhook_listener import run_webhook_listener
from commands import SeasonCommands

intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Create instances of your managers
season_manager = SeasonManager(bot)
weather_manager = WeatherManager(bot)
water_manager = WaterManager()

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

    try:
        # Use the GUILD_ID from your config/env
        if GUILD_ID != 0:
            guild = discord.Object(id=1302597482274095227)
            synced = await bot.tree.sync(guild=guild)
            print(f"Synced {len(synced)} slash commands to guild {GUILD_ID}.")
        else:
            # Fallback to global sync if GUILD_ID=0 or missing
            synced = await bot.tree.sync()
            print(f"Synced {len(synced)} slash commands globally.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    await bot.add_cog(SeasonCommands(bot))

    await season_manager.check_season_change()
    await weather_manager.start_weather_loop()
    await water_manager.start_water_loop()

    asyncio.create_task(run_webhook_listener(bot))

bot.run(BOT_TOKEN)
