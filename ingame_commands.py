import json
import random
import time
from mcrcon import MCRcon

AUTHORIZED_IDS = {"323-305-595", "045-616-395"}
ADMIN_ONLY_COMMANDS = {"!tparbour", "!tpyaga", "!tpshaded", "!tpvalkov", "!tpbogwitch"}

TP_COORDINATES = {
    "!redisland": [
        "x=50676 y=312304 z=-3042",
        "x=-54464 y=327838 z=1422",
        "x=-85760 y=350807 z=-3288"
    ],
    "!whitecliffs": [
        "x=-227628 y=-103155 z=1215",
        "x=-222949 y=-97014 z=3073",
        "x=-220150 y=-106305 z=-3986"
    ],
    "!whistling": [
        "x=-44054 y=195274 z=-2559",
        "x=-51945 y=185067 z=-2244",
        "x=-25180 y=195142 z=181"
    ]
}

ADMIN_TP_COORDS = {
    "!tparbour": "x=-298134 y=-64097 z=-2734",
    "!tpyaga": "x=-154056 y=136070 z=907",
    "!tpvalkov": "x=-122689 y=79773 z=2043",
    "!tpbogwitch": "x=-59631 y=-107544 z=-937",
    "!tpshaded": "0 0 0"
}

RESPAWN_COOLDOWNS = {}
RESPAWN_COOLDOWN_SECONDS = 3600
LOG_CHANNEL_ID = 1359506060414812284
bot_instance = None

def set_bot(bot):
    global bot_instance
    bot_instance = bot

def whisper(mcr, user_id, text):
    mcr.command(f"/whisper {user_id} {text}")

async def handle_ingame_command(message: str, user_id: str):
    message = message.strip().lower()

    try:
        with open("config.json", "r") as f:
            config = json.load(f)

        rcon = config["rcon"]

        with MCRcon(rcon["host"], rcon["password"], port=rcon["port"]) as mcr:
            if message == "!pingme":
                whisper(mcr, user_id, "Ping received. Bot is connected and listening.")

            elif message in ADMIN_ONLY_COMMANDS and user_id not in AUTHORIZED_IDS:
                return

            elif message in TP_COORDINATES:
                coords = random.choice(TP_COORDINATES[message])
                mcr.command(f"/teleport ({coords})")
                whisper(mcr, user_id, f"You have been teleported to {message[1:].capitalize()}.")

            elif message == "!freezehealth":
                mcr.command("/setattr HealthRecoveryRate 0")
                whisper(mcr, user_id, "Passive health recovery stopped.")

            elif message == "!freezestam":
                mcr.command("/setattr StaminaRecoveryRate 0")
                whisper(mcr, user_id, "Passive stamina recovery stopped.")

            elif message == "!respawn":
                now = time.time()
                if user_id in RESPAWN_COOLDOWNS and now - RESPAWN_COOLDOWNS[user_id] < RESPAWN_COOLDOWN_SECONDS:
                    remaining = int(RESPAWN_COOLDOWNS[user_id] + RESPAWN_COOLDOWN_SECONDS - now)
                    whisper(mcr, user_id, f"Respawn is on cooldown. Try again in {remaining // 60} min.")
                else:
                    mcr.command("/respawn")
                    whisper(mcr, user_id, "You have been respawned.")
                    RESPAWN_COOLDOWNS[user_id] = now

            elif message.startswith("!setgrowth"):
                try:
                    value = float(message.split()[1])
                    if not 0 <= value <= 0.99:
                        whisper(mcr, user_id, "Growth must be between 0.0 and 0.99.")
                        return

                    mcr.command(f"/setattr growth {value}")
                    mcr.command("/setattr GrowthPerSecond 0")
                    whisper(mcr, user_id, f"Growth set to {value}. Growth is frozen! To unfreeze, relog character.")

                    if bot_instance:
                        log_channel = bot_instance.get_channel(LOG_CHANNEL_ID)
                        if log_channel:
                            await log_channel.send(f"🧬 Growth set in-game by `{user_id}` → `{value}` (frozen).")

                except Exception as e:
                    print(e)
                    whisper(mcr, user_id, "Usage: !setgrowth <0.0 - 0.99>")

            elif message in ADMIN_ONLY_COMMANDS:
                coords = ADMIN_TP_COORDS.get(message, "0 0 0")
                mcr.command(f"/teleport ({coords})")
                whisper(mcr, user_id, f"Teleporting to {message[3:].capitalize()}.")

    except Exception as e:
        print(f"[In-game Command Error] {e}")
        if bot_instance:
            log_channel = bot_instance.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(f"⚠️ Error in handle_ingame_command: {e}")
