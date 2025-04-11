from config import CHANNEL_IDS

async def log_to_discord(bot, message: str):
    """
    Sends a log message to the #bot-logs channel on Discord.
    If bot is None (or the channel isn't found), it prints to console instead.
    """
    # If the bot reference is missing, just print.
    if not bot:
        print(f"[LOG - no bot reference]: {message}")
        return

    channel = bot.get_channel(CHANNEL_IDS["bot_logs"])
    if channel:
        await channel.send(message)
    else:
        print(f"[LOG - channel not found]: {message}")
