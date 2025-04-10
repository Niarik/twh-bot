# ingame_commands.py
import asyncio
import json
from discord.ext import tasks
from mcrcon import MCRcon
from weather_cycle import pause_weather_for, resume_weather

AUTHORIZED_IDS = {"323-305-595", "045-616-395"}
last_checked_message = ""
bot_instance = None
LOG_CHANNEL_ID = 1359506060414812284

def set_bot(bot):
    global bot_instance
    bot_instance = bot

@tasks.loop(seconds=5)
async def poll_ingame_chat():
    try:
        with open("config.json", "r") as f:
            config = json.load(f)

        rcon = config["rcon"]

        with MCRcon(rcon["host"], rcon["password"], port=rcon["port"]) as mcr:
            output = mcr.command("/getchat")

            if not output:
                return

            global last_checked_message
            lines = output.strip().split("\n")
            new_lines = [line for line in lines if line != last_checked_message and line.strip() != ""]

            for line in new_lines:
                last_checked_message = line
                print(f"[Chat Check] {line}")

                parts = line.split(": ", 1)
                if len(parts) < 2:
                    continue

                header, message = parts
                if any(admin_id in header for admin_id in AUTHORIZED_IDS):
                    message = message.strip().lower()

                    if message == "!pauseweather":
                        pause_weather_for(4)
                        mcr.command("say Weather has been paused for 4 hours by an admin.")
                        if bot_instance:
                            log = bot_instance.get_channel(LOG_CHANNEL_ID)
                            if log:
                                await log.send("🛑 In-game command: Weather paused for 4 hours.")

                    elif message == "!startweather":
                        resume_weather()
                        mcr.command("say Weather updates have resumed.")
                        if bot_instance:
                            log = bot_instance.get_channel(LOG_CHANNEL_ID)
                            if log:
                                await log.send("▶️ In-game command: Weather system restarted.")

    except Exception as e:
        print(f"[In-game Chat Error] {e}")