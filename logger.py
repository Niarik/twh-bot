#logger.py
from config import CHANNEL_IDS

async def log_to_discord(bot, message):
    channel = bot.get_channel(CHANNEL_IDS["bot_logs"])
    if channel:
        await channel.send(message)
