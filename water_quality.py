import json
from discord.ext import tasks
from datetime import datetime
from mcrcon import MCRcon
from seasons import get_current_season
from os import getenv

HOTSPRING_LOCATIONS = [
    "Hotspring1", "Hotspring2", "Hotspring3", "Hotspring4", "Hotspring5", "Hotspring6",
    "Hotspring7", "Hotspring8", "Hotspring9", "Hotspring10", "Hotspring11", "Hotspring12",
    "Hotspring13", "Hotspring14", "Hotspring15", "Hotspring16", "Hotspring17", "Hotspring18",
    "Hotspring19", "Hotspring20", "Hotspring21", "Hotspring22", "Hotspring23", "Hotspring24"
]

PARTIAL_WATER_LOCATIONS = [
    "TriadFalls", "WhistlingLake", "TitansPassLake", "BigQuillLake", "HuntersThicket",
    *HOTSPRING_LOCATIONS, "WhiteCliffs", "GreenValley", "RockfallHill"
]

ALL_LOCATIONS = [
    "YoungGroveLake", "PutridLake", "TitansPassLake", "TriadFalls", "WhistlingColumns",
    "HuntersThicket", "BigQuillLake", "RockfallHill", "BrokenToothPond", "FrogPond",
    "HoodooPond", "LowerStegoPond", "DarkwoodsPond", "UpperStegoPond", "ImpactCrater",
    "RedIsland", "ReedPond2", "MountainScubPond", "SharptoothPond", "AcridLake",
    "ReedPondSouth", "BirchwoodsPond", "BurnedForestPond", "GreenValley", "WhiteCliffsLake",
    "TriadPond", "BaldMountainPond", "RainbowPond", "WildernessPeakPond", "YoungGrovePond",
    *HOTSPRING_LOCATIONS
]

def send(location, value):
    try:
        with MCRcon(
            getenv("RCON_HOST"),
            getenv("RCON_PASSWORD"),
            port=int(getenv("RCON_PORT"))
        ) as mcr:
            mcr.command(f"/waterquality {location} {value}")
            print(f"Set waterquality {location} {value}")
    except Exception as e:
        print(f"Failed to set water quality: {e}")

@tasks.loop(hours=3)
async def update_water_quality():
    season = get_current_season()

    if season == "the drought":
        for loc in ALL_LOCATIONS:
            value = 40 if loc in PARTIAL_WATER_LOCATIONS else 0
            send(loc, value)

    elif season == "the freeze":
        for loc in ALL_LOCATIONS:
            value = 100 if loc in PARTIAL_WATER_LOCATIONS else 0
            send(loc, value)

    elif season == "the brightening":
        for loc in ALL_LOCATIONS:
            send(loc, 100)

    else:
        print("No water update needed for this season.")
