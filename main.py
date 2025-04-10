import os
import discord
from discord.ext import commands
from weather_cycle import start_season_schedule
from ingame_commands import handle_ingame_command, set_bot
from seasons import post_season_announcement, get_current_season, get_current_season_times

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    set_bot(bot)
    poll_ingame_chat.start()  # Starts the in-game chat listener
    start_season_schedule(bot)
    await post_season_announcement(bot, get_current_season(), 1303375972258812036)

    # Debug info
    start_time, end_time = get_current_season_times()
    print(f"Season started: {start_time} → Ends: {end_time}")

@bot.event
async def on_message(message):
    # Don't let the bot respond to its own messages
    if message.author == bot.user:
        return

    # Only process messages from the webhook channel
    if message.channel.id == 1303344696096985120:  # The webhook channel ID
        # Extract the necessary fields from the message
        message_content = message.content
        if "Message:" in message_content:
            command_message = message_content.split("Message:")[1].split("\n")[0].strip()  # Extract !pingme or other commands
            user_id = message_content.split("AlderonId:")[1].split("\n")[0].strip()  # Extract player ID
            
            if command_message.startswith("!"):
                print(f"Received command: {command_message} from {user_id}")
                
                # Handle specific commands
                if command_message == "!pingme":
                    # Respond to the player in-game with a whisper
                    mcr.command(f"/whisper {user_id} Ping received. Bot is connected and listening.")

bot.run(os.getenv("BOT_TOKEN"))
