import asyncio
from discord.ext import commands
from discord import Intents
from config import BOT_TOKEN
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

    # Register (sync) slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    # Add our slash commands
    await bot.add_cog(SeasonCommands(bot))

    # Immediately check if the season needs to change
    await season_manager.check_season_change()

    # Start the weather and water loops
    await weather_manager.start_weather_loop()
    await water_manager.start_water_loop()

    # Start the webhook listener (for in-game commands)
    asyncio.create_task(run_webhook_listener(bot))

bot.run(BOT_TOKEN)
