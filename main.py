# main.py
import os
import discord
from discord.ext import commands
from weather_cycle import start_season_schedule
from ingame_commands import poll_ingame_chat, set_bot
from seasons import post_season_announcement, get_current_season, get_current_season_times

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    set_bot(bot)
    poll_ingame_chat.start()  # 🟢 In-game chat commands listener
    start_season_schedule(bot)
    await post_season_announcement(bot, get_current_season(), 1303375972258812036)

    # Debug info
    start_time, end_time = get_current_season_times()
    print(f"Season started: {start_time} → Ends: {end_time}")

bot.run(os.getenv("BOT_TOKEN"))
