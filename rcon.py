#rcon.py
import asyncio
from config import RCON_HOST, RCON_PORT, RCON_PASSWORD
from mcrcon import MCRcon

# This needs to run in a thread because MCRcon is synchronous
async def send_rcon_command(command: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _send_rcon_blocking, command)

def _send_rcon_blocking(command: str):
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            response = mcr.command(command)
            return response
    except Exception as e:
        print(f"RCON command failed: {e}")
        return None
