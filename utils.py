import discord
import re

# Parses a webhook-formatted message like:
# "[PlayerName] /command argument"
def parse_command(message_content):
    match = re.match(r"\[(.*?)\]\s*/(\w+)\s*(.*)", message_content)
    if not match:
        return None, None, None  # Not a valid command format

    player_name, command, args = match.groups()
    args = args.strip()
    return player_name, command.lower(), args


# Sends a message to the given Discord text channel
async def send_to_channel(bot, channel_id, message):
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(message)
    else:
        print(f"[Error] Could not find channel with ID {channel_id}")


# Sends a season announcement (detailed version)
async def announce_season(bot, channel_id, season_name, season_times):
    start_str = season_times["start"].strftime("%b %d")
    end_str = season_times["end"].strftime("%b %d")

    embed = discord.Embed(
        title=f"🌿 New Season: {season_name}",
        description=f"**Duration:** {start_str} to {end_str}",
        color=discord.Color.green()
    )
    embed.set_footer(text="Stay hydrated. Or don't.")

    await send_to_channel(bot, channel_id, embed)
