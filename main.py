# main.py
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from seasons import post_season_announcement, get_current_season, get_current_season_times, season_data, SEASON_LENGTH_DAYS
from weather_cycle import cycle_weather, pause_weather_for, resume_weather, set_bot
from water_quality import update_water_quality
import datetime
import importlib
import os

config = {
    "rcon": {
        "host": os.getenv("RCON_HOST"),
        "port": int(os.getenv("RCON_PORT")),
        "password": os.getenv("RCON_PASSWORD")
    },
    "interval_minutes": 20,
    "announce_channel_id": 1303375972258812036,
    "log_channel_id": 1359506060414812284
}

from ingame_commands import poll_ingame_chat, set_bot as set_ingame_bot


intents = discord.Intents.default()
intents.message_content = False
bot = commands.Bot(command_prefix="/", intents=intents)

SEASON_CHANNEL_ID = 1303375972258812036
LOG_CHANNEL_ID = 1359506060414812284
SEASON_ROTATION_START = datetime.datetime(2025, 4, 9, 12, 0, 0)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    set_bot(bot)  # from weather_cycle
    set_ingame_bot(bot)  # from ingame_commands ✅
    await post_season_announcement(bot, get_current_season(), SEASON_CHANNEL_ID)
    cycle_weather.start()
    update_water_quality.start()
    poll_ingame_chat.start()  # start listening to in-game chat
    await bot.tree.sync()


@bot.tree.command(name="pauseweather", description="Pause weather updates for 4 hours")
@app_commands.checks.has_permissions(administrator=True)
async def pauseweather(interaction: discord.Interaction):
    pause_weather_for(4)
    resume_time = int((datetime.datetime.now() + datetime.timedelta(hours=4)).timestamp())
    await interaction.response.send_message(f"✅ Weather changes paused until <t:{resume_time}:F>.")
    log = bot.get_channel(LOG_CHANNEL_ID)
    if log:
        await log.send(f"🛑 Weather paused by {interaction.user.display_name} until <t:{resume_time}:F>.")

@bot.tree.command(name="startweather", description="Resume weather updates immediately")
@app_commands.checks.has_permissions(administrator=True)
async def startweather(interaction: discord.Interaction):
    resume_weather()
    await interaction.response.send_message("✅ Weather changes resumed.")
    log = bot.get_channel(LOG_CHANNEL_ID)
    if log:
        await log.send(f"▶️ Weather resumed by {interaction.user.display_name}.")

@bot.tree.command(name="seasonstatus", description="Check the current season and when it ends")
async def seasonstatus(interaction: discord.Interaction):
    season = get_current_season()
    times = get_current_season_times()
    start_ts = int(times["start_time"].timestamp())
    end_ts = int(times["end_time"].timestamp())
    embed = discord.Embed(title=f"Current Season: {season.title()}", color=0x5dade2)
    embed.add_field(name="Start", value=f"<t:{start_ts}:F>", inline=True)
    embed.add_field(name="End", value=f"<t:{end_ts}:F>", inline=True)
    embed.set_footer(text="Season auto-rotates every 2 weeks.")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="nextseason", description="Advance to the next season (for testing)")
@app_commands.checks.has_permissions(administrator=True)
async def nextseason(interaction: discord.Interaction):
    global SEASON_ROTATION_START
    SEASON_ROTATION_START -= datetime.timedelta(days=SEASON_LENGTH_DAYS)
    await post_season_announcement(bot, get_current_season(), SEASON_CHANNEL_ID)
    await interaction.response.send_message(f"✅ Season forced forward to **{get_current_season().title()}**.")
    log = bot.get_channel(LOG_CHANNEL_ID)
    if log:
        await log.send(f"⏭️ Season manually advanced by {interaction.user.display_name}.")

@bot.tree.command(name="seasonreset", description="Reset the season cycle to start today with The Blooming")
@app_commands.checks.has_permissions(administrator=True)
async def seasonreset(interaction: discord.Interaction):
    global SEASON_ROTATION_START
    SEASON_ROTATION_START = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
    await post_season_announcement(bot, get_current_season(), SEASON_CHANNEL_ID)
    await interaction.response.send_message("🔄 Season cycle has been reset to start now.")
    log = bot.get_channel(LOG_CHANNEL_ID)
    if log:
        await log.send(f"🔁 Season cycle reset by {interaction.user.display_name}.")

@bot.tree.command(name="helpweather", description="Show a list of weather bot commands and what they do")
async def helpweather(interaction: discord.Interaction):
    embed = discord.Embed(title="TWH Weather Bot – Help", color=0x00bfff)
    embed.add_field(name="/seasonstatus", value="Shows the current season and when it ends.", inline=False)
    embed.add_field(name="/pauseweather", value="⛔ Admin only – pauses weather updates for 4 hours.", inline=False)
    embed.add_field(name="/startweather", value="▶️ Admin only – resumes weather updates immediately.", inline=False)
    embed.add_field(name="/nextseason", value="⏭️ Admin only – skips forward to the next season.", inline=False)
    embed.add_field(name="/seasonreset", value="🔁 Admin only – resets the season cycle to start today.", inline=False)
    embed.add_field(name="/reloadsettings", value="🔃 Admin only – reloads config/settings without restarting.", inline=False)
    embed.set_footer(text="Bot created for The Wild Hunt RP server.")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="reloadsettings", description="Reload config and season data without resetting state")
@app_commands.checks.has_permissions(administrator=True)
async def reloadsettings(interaction: discord.Interaction):
    try:
        importlib.reload(json)
        importlib.reload(importlib.import_module("seasons"))
        importlib.reload(importlib.import_module("weather_cycle"))
        importlib.reload(importlib.import_module("water_quality"))
        await interaction.response.send_message("🔃 Config and seasonal data reloaded (soft refresh).", ephemeral=True)
        log = bot.get_channel(LOG_CHANNEL_ID)
        if log:
            await log.send(f"🔃 Config and data reloaded by {interaction.user.display_name}.")
    except Exception as e:
        await interaction.response.send_message(f"❌ Reload failed: {e}", ephemeral=True)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("🚫 You don’t have permission to use this command.", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ Something went wrong.", ephemeral=True)

bot.run(os.getenv("BOT_TOKEN"))
