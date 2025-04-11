from discord.ext import commands
from discord import app_commands, Interaction
import discord
import datetime
from storage import (
    get_last_season, get_last_weather,
    set_pause_state, get_pause_state
)
from logger import log_to_discord

class SeasonCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="seasoninfo", description="Show current season and weather")
    async def season_info(self, interaction: Interaction):
        """
        Displays the current season, when it started, when it ends, 
        and the current weather (if known).
        """
        season_data = get_last_season()
        weather = get_last_weather() or "Unknown"

        if not season_data:
            await interaction.response.send_message("No season data available yet.", ephemeral=True)
            return

        season = season_data.get("season")
        start_str = season_data.get("start")
        start_dt = datetime.datetime.fromisoformat(start_str)
        end_dt = start_dt + datetime.timedelta(days=14)

        start_fmt = discord.utils.format_dt(start_dt, style='F')
        end_fmt = discord.utils.format_dt(end_dt, style='F')
        end_rel = discord.utils.format_dt(end_dt, style='R')

        embed = discord.Embed(
            title=f"Current Season: {season}",
            description=(
                f"**Season Started:** {start_fmt}\n"
                f"**Season Ends:** {end_fmt} ({end_rel})\n"
                f"**Current Weather:** {weather}"
            ),
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pauseweather", description="Pause weather updates for 4 hours")
    async def pause_weather(self, interaction: Interaction):
        """
        Admin-only command that pauses the weather cycle for 4 hours.
        After 4 hours, it auto-resumes.
        """
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You must be an admin to use this command.", ephemeral=True)
            return

        set_pause_state(True)

        # Auto-resume after 4 hours
        async def auto_resume():
            await discord.utils.sleep_until(
                datetime.datetime.utcnow() + datetime.timedelta(hours=4)
            )
            set_pause_state(False)
            await log_to_discord(self.bot, "Weather auto-resumed after 4-hour pause.")

        self.bot.loop.create_task(auto_resume())

        await interaction.response.send_message("Weather updates paused for 4 hours.")
        await log_to_discord(self.bot, f"Weather paused by {interaction.user.name} for 4 hours.")

    @app_commands.command(name="restartweather", description="Resume weather updates immediately")
    async def restart_weather(self, interaction: Interaction):
        """
        Admin-only command to resume weather changes immediately.
        """
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You must be an admin to use this command.", ephemeral=True)
            return

        set_pause_state(False)
        await interaction.response.send_message("Weather updates resumed.")
        await log_to_discord(self.bot, f"Weather resumed manually by {interaction.user.name}.")
