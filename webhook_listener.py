import os
import asyncio
import json
from aiohttp import web
from rcon import send_rcon_command
from logger import log_to_discord

# Example dictionary of teleports:
TELEPORT_LOCATIONS = {
    "redisland":  {"x":1234, "y":5678, "z":1256},
    "whitecliffs": {"x":2345, "y":6789, "z":1357},
    "whistling":   {"x":3456, "y":7890, "z":2468},
    "saltflats":   {"x":4567, "y":8901, "z":3579},
    "yaga":        {"x":5678, "y":9012, "z":4680},
    "arbour":      {"x":6123, "y":1011, "z":5791},
    "shaded":      {"x":7234, "y":1122, "z":6802},
    "bogwitch":    {"x":8345, "y":1233, "z":7913},
    "valkov":      {"x":9456, "y":1344, "z":8024},
}

async def run_webhook_listener(bot):
    """
    Starts an aiohttp server on port 8080 to receive messages from your game server.
    Expects JSON body { 'username': '...', 'message': '...' }.
    If you want a different format, edit handle_webhook() accordingly.
    """

    async def handle_webhook(request):
        try:
            data = await request.json()
        except json.decoder.JSONDecodeError:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        username = data.get("username", "Unknown")
        message = data.get("message", "").strip()
        if not message.startswith("!"):
            # Not a bot command
            return web.json_response({"status": "ignored"})

        # Process the command
        reply = await process_in_game_command(bot, username, message)
        return web.json_response({"status": "ok", "reply": reply})

    # Create the aiohttp app and route
    app = web.Application()
    app.router.add_post("/", handle_webhook)

    # Start the server on port 8080 (or use PORT from environment)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    print(f"[Webhook Listener] Listening on port {port}")

async def process_in_game_command(bot, username: str, message: str):
    """
    Parses the in-game command like '!redisland' or '!freezehealth',
    sends RCON commands, and logs as needed.
    """
    # Convert everything to lowercase for matching, but keep original for messages
    cmd = message.lower().split()

    # TELEPORTS: e.g. !redisland -> /teleport x=1234 y=5678 z=1256
    if cmd[0].startswith("!"):
        base_cmd = cmd[0][1:]  # remove '!'
        if base_cmd in TELEPORT_LOCATIONS:
            coords = TELEPORT_LOCATIONS[base_cmd]
            rcon_command = f"/teleport x={coords['x']} y={coords['y']} z={coords['z']}"
            await send_rcon_command(rcon_command)
            await send_rcon_command(f"/systemmessage Teleporting {username} to {base_cmd}")
            await log_to_discord(bot, f"{username} teleported to {base_cmd}")
            return f"Teleported to {base_cmd}"

    # FREEZE HEALTH: !freezehealth -> /setattr HealthRecoveryRate 0
    if cmd[0] == "!freezehealth":
        await send_rcon_command("/setattr HealthRecoveryRate 0")
        await send_rcon_command(f"/systemmessage Health regen frozen for {username}")
        await log_to_discord(bot, f"{username} used freezehealth")
        return "Health regeneration frozen."

    # FREEZE STAMINA: !freezestam -> /setattr StaminaRecoveryRate 0
    if cmd[0] == "!freezestam":
        await send_rcon_command("/setattr StaminaRecoveryRate 0")
        await send_rcon_command(f"/systemmessage Stamina regen frozen for {username}")
        await log_to_discord(bot, f"{username} used freezestam")
        return "Stamina regeneration frozen."

    # SET GROWTH: !setgrowth 0.7 -> /setattr growth 0.7 then /setattra GrowthPerSecond 0
    if cmd[0] == "!setgrowth":
        if len(cmd) < 2:
            return "Usage: !setgrowth <0.0 - 1.0>"
        try:
            growth_val = float(cmd[1])
        except ValueError:
            return "Invalid growth value. Must be a float between 0.0 and 1.0"
        if 0.0 <= growth_val <= 1.0:
            await send_rcon_command(f"/setattr growth {growth_val}")
            await send_rcon_command("/setattra GrowthPerSecond 0")
            await send_rcon_command(f"/systemmessage Growth set to {growth_val} for {username}")
            await log_to_discord(bot, f"{username} used setgrowth {growth_val}")
            return f"Growth set to {growth_val} and frozen."
        else:
            return "Growth must be between 0.0 and 1.0"

    # PING ADMIN: !pingme -> Admin-only example
    # NOTE: We don't have a real "admin check" here. Just an example.
    # You might want to compare 'username' with a known admin list or your server's data.
    if cmd[0] == "!pingme":
        is_admin = (username.lower() in ["youradminusername"])  # example
        if not is_admin:
            return "You are not allowed to use this admin command."
        await send_rcon_command(f"/systemmessage PING from {username}")
        await log_to_discord(bot, f"{username} used !pingme")
        return "Pong! (admin verified)"

    # If we reach here, none of the commands matched
    return "Command not recognized."
