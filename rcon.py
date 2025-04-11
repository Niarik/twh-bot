#rcon.py
import asyncio
from aiorcon import RCON
from config import RCON_HOST, RCON_PORT, RCON_PASSWORD

async def send_rcon_command(cmd):
    async with RCON(RCON_HOST, RCON_PORT, RCON_PASSWORD) as rcon:
        await rcon.command(cmd)
