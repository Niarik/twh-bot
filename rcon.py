import asyncio
from config import RCON_HOST, RCON_PORT, RCON_PASSWORD
from mcrcon import MCRcon

async def send_rcon_command(command: str):
    """
    Allows you to send an RCON command asynchronously.
    We'll run the blocking MCRcon call in a thread executor,
    so it doesn't block our async bot.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _send_rcon_blocking, command)

def _send_rcon_blocking(command: str):
    """
    Blocking RCON call: 
    Connects to the server, sends command, disconnects.
    Returns the server's response if successful, or None if it fails.
    """
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            response = mcr.command(command)
            return response
    except Exception as e:
        print(f"[RCON ERROR] Failed to send '{command}': {e}")
        return None
