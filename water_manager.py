import asyncio
import datetime
from storage import get_last_season
from logger import log_to_discord
from rcon import send_rcon_command  # uses your rcon.py

class WaterManager:
    def __init__(self):
        self.interval = 3 * 60 * 60  # 3 hours in seconds

        # All known water sources
        self.all_sources = [
            "YoungGroveLake", "PutridLake", "TitansPassLake", "TriadFalls", "WhistlingColumns",
            "HuntersThicket", "BigQuillLake", "RockfallHill", "BrokenToothPond", "FrogPond",
            "HoodooPond", "LowerStegoPond", "DarkwoodsPond", "UpperStegoPond", "ImpactCrater",
            "RedIsland", "ReedPond2", "MountainScubPond", "SharptoothPond", "AcridLake",
            "ReedPondSouth", "BirchwoodsPond", "BurnedForestPond", "GreenValley", "WhiteCliffsLake",
            "TriadPond", "BaldMountainPond", "RainbowPond", "WildernessPeakPond", "YoungGrovePond",
            "Hotspring1", "Hotspring2", "Hotspring3", "Hotspring4", "Hotspring5", "Hotspring6",
            "Hotspring7", "Hotspring8", "Hotspring9", "Hotspring10", "Hotspring11", "Hotspring12",
            "Hotspring13", "Hotspring14", "Hotspring15", "Hotspring16", "Hotspring17", "Hotspring18",
            "Hotspring19", "Hotspring20", "Hotspring21", "Hotspring22", "Hotspring23", "Hotspring24"
        ]

        # 'Major' water sources
        self.major_sources = [
            "YoungGroveLake", "PutridLake", "BigQuillLake", "TriadFalls",
            "HuntersThicket", "GreenValley"
        ]

        # Hotsprings
        self.hotsprings = [f"Hotspring{i}" for i in range(1, 25)]

    async def start_water_loop(self):
        """
        Main loop that waits 3 hours, 
        then applies water logic based on the current season.
        """
        while True:
            await self.apply_water_logic()
            await asyncio.sleep(self.interval)

    async def apply_water_logic(self):
        """
        Reads the current season, then issues water quality commands via RCON.
        """
        season_info = get_last_season()
        if not season_info:
            return

        season = season_info["season"]
        commands = []

        if season == "The Blooming":
            # No changes
            await log_to_discord(None, "[Water Manager] Blooming - no water quality changes.")
            return

        elif season == "The Drought":
            # All water 0, but major sources 40
            for source in self.all_sources:
                quality = 40 if source in self.major_sources else 0
                commands.append(f"/waterquality {source} {quality}")

        elif season == "The Brightening":
            # All water sources 100
            for source in self.all_sources:
                commands.append(f"/waterquality {source} 100")

        elif season == "The Freeze":
            # Major + hotsprings => 50; others => 0
            for source in self.all_sources:
                if source in self.major_sources or source in self.hotsprings:
                    commands.append(f"/waterquality {source} 50")
                else:
                    commands.append(f"/waterquality {source} 0")

        for cmd in commands:
            await send_rcon_command(cmd)

        await log_to_discord(None, f\"[Water Manager] Applied {len(commands)} water quality updates for {season}\")
