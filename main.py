import os
import json
import discord
from discord.ext import commands
from mcrcon import MCRcon
from weather_cycle import start_season_schedule
from ingame_commands import handle_ingame_command, set_bot
from seasons import post_season_announcement, get_current_season, get_current_season_times
from weather_cycle import pause_weather_for, resume_weather

# Load RCON credentials from environment
RCON_HOST = os.getenv("RCON_HOST")
RCON_PORT = int(os.getenv("RCON_PORT"))
RCON_PASSWORD = os.getenv("RCON_PASSWORD")

# Load non-sensitive config from config.json
with open("config.json", "r") as f:
    config = json.load(f)

INTERVAL_MINUTES = config["interval_minutes"]
ANNOUNCE_CHANNEL_ID = config["announce_channel_id"]
LOG_CHANNEL_ID = config["log_channel_id"]

# Set up bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    set_bot(bot)
    start_season_schedule()
    await post_season_announcement(bot, get_current_season(), ANNOUNCE_CHANNEL_ID)

    # Debug info
    start_time, end_time = get_current_season_times()
    print(f"🗓️ Season started: {start_time} → Ends: {end_time}")

@bot.event
async def on_message(message):
    # Ignore the bot's own messages
    if message.author == bot.user:
        return

    # Process only messages from the game webhook channel
    if message.channel.id == 1303344696096985120:  # Replace with your actual webhook channel ID
        message_content = message.content
        if "Message:" in message_content:
            command_message = message_content.split("Message:")[1].split("\n")[0].strip()
            user_id = message_content.split("AlderonId:")[1].split("\n")[0].strip()

            if command_message.startswith("!"):
                print(f"📥 Received command: {command_message} from {user_id}")

                if command_message == "!pingme":
                    try:
                        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                            mcr.command(f"/systemmessage {user_id} Ping received. Bot is connected and listening.")
                    except Exception as e:
                        print(f"[RCON Error] Could not send ping reply: {e}")

                elif command_message == "!testing":
                    await message.channel.send(f"✅ Testing message received from `{user_id}`.")

                else:
                    # Optional: pass unrecognized commands to the ingame handler
                    await handle_ingame_command(message)

@bot.command()
async def pauseweather(ctx, hours: int = 4):
    """Pauses weather updates for a set number of hours (default 6)."""
    pause_weather_for(hours)
    await ctx.send(f"⏸️ Weather updates paused for {hours} hour(s).")

@bot.command()
async def resumeweather(ctx):
    """Resumes weather updates immediately."""
    resume_weather()
    await ctx.send("▶️ Weather updates resumed.")

@bot.command()
async def seasonstatus(ctx):
    """Displays the current season, timing, current weather, and last weather change."""
    current_season = get_current_season()
    times = get_current_season_times()
    start_time = times['start_time']
    end_time = times['end_time']

    # Retrieve weather info
    from weather_cycle import get_weather_info
    current_weather, last_weather_change = get_weather_info()

    # Format last weather change time
    last_change_str = last_weather_change.strftime("%Y-%m-%d %H:%M:%S") if last_weather_change else "unknown"

    await ctx.send(f"🗓️ Current season: **{current_season.title()}**\n"
                   f"Start: **{start_time}**\n"
                   f"End: **{end_time}**\n\n"
                   f"🌤️ Current weather: **{current_weather}**\n"
                   f"Last weather change: **{last_change_str}**")

bot.run(os.getenv("BOT_TOKEN"))
