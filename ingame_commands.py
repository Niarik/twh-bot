async def handle_ingame_command(message: str, user_id: str):
    message = message.strip().lower()

    try:
        import os

        with MCRcon(
            os.getenv("RCON_HOST"),
            os.getenv("RCON_PASSWORD"),
            port=int(os.getenv("RCON_PORT"))
        ) as mcr:

            if message == "!pingme":
                whisper(mcr, user_id, "Ping received. Bot is connected and listening.")

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
                parts = message.split()
                if len(parts) == 2:
                    try:
                        growth = float(parts[1])
                        if 0 <= growth <= 1:
                            mcr.command(f"/setattr {user_id} growth {growth}")
                            mcr.command(f"/setattr {user_id} GrowthPerSecond 0")
                            whisper(mcr, user_id, f"Growth set to {growth} and frozen.")
                        else:
                            whisper(mcr, user_id, "Growth must be between 0 and 1.")
                    except ValueError:
                        whisper(mcr, user_id, "Please use a valid number like `!setgrowth 0.85`.")
                else:
                    whisper(mcr, user_id, "Usage: !setgrowth 0.85")

    except Exception as e:
        print(f"[In-game Command Error] {e}")
        if bot_instance:
            log_channel = bot_instance.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(f"⚠️ Error in handle_ingame_command: {e}")
