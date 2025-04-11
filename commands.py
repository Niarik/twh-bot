#commands.py
from discord.ext import commands
from discord import app_commands

class SeasonCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="seasoninfo")
    async def season_info(self, interaction):
        # Get data from storage and reply with season/weather info
        pass

    @app_commands.command(name="pauseweather")
    async def pause_weather(self, interaction):
        # Pause weather updates for 4 hours
        pass

    @app_commands.command(name="restartweather")
    async def restart_weather(self, interaction):
        # Resume weather updates immediately
        pass
