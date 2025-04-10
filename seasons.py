# seasons.py
import discord
import json
import os
from datetime import datetime, timedelta

season_data = {
    "the blooming": {
        "weather_options": ["rain", "cloudy", "storm", "fog", "overcast"],
        "description": "The last of the snow has finally thawed, warm rain sweeps in and keeps water sources full to bursting and food sources plentiful. Chilly mornings and evenings are accompanied by thick fog, the weather varies from lengthy storms to brief showers. When the rain clears, it is cloudy and overcast, but the days are warm enough for most species to begin their first wave of nesting, hoping to raise their hatchlings enough to get them through the coming drought.",
        "banner": "theblooming.png",
        "emoji": "🌸",
        "announcement": "🌸 **The Blooming has arrived** 🌸\n\n- The weather is warm, rainy, stormy, overcast and cloudy\n- Water and food are abundant"
    },
    "the drought": {
        "weather_options": ["clearsky", "cloudy"],
        "description": "The drought is a true survival test for most species, as the rains disappear and the water sources dry up. Rare storms bring some relief, but most species will have to move often and venture outside of their territories to find enough water to survive. Hatchlings born in this season face enormous challenges and rarely make it to The Brightening.",
        "banner": "thedrought.png",
        "emoji": "🔥",
        "announcement": "🔥 **The Drought has arrived** 🔥\n\n- Water is scarce and doesn't regenerate automatically, but all water sources will still replenish to low levels of quality, with larger water sources replenishing to 60% every few hours.\n- The cool and damp of The Blooming has left small pools in some caves in arid areas that the oppressive heat can't reach\n- Wildfires may occur"
    },
    "the brightening": {
        "weather_options": ["clearsky", "cloudy", "overcast"],
        "description": "The Brightening is the comfortably warm season following the drought. The weather is typically clear and bright, with periodic rains keeping water sources flowing and food plentiful. Many species will have a second wave of nests during this season, the last of the year. Towards the end of the season, most species will settle into territories they can stay in for The Freeze.",
        "banner": "thebrightening.png",
        "emoji": "☀️",
        "announcement": "🌞 **The Brightening has arrived** 🌞\n\n- The heat of the drought has eased but the weather remains clear\n- Water sources have been replenished by periodic rains and the heat is not enough to deplete them\n- The next wave of nesting has arrived for many species"
    },
    "the freeze": {
        "weather_options": ["snow", "fog", "overcast"],
        "description": "During The Freeze, frosts are soon followed by thick snowfall, the temperature turns bitterly cold, many plants go dormant and water sources freeze over. Water is still accessible for large species who can break the ice, but some herds may have to periodically travel in search of roots and nuts. Carnivores are particularly dangerous during The Freeze, driven from their winter dens only by extreme hunger.",
        "banner": "thefreeze.png",
        "emoji": "❄️",
        "announcement": "❄️ **The Freeze has arrived** ❄️\n\n- The weather is cold, snowy and foggy\n- Small water sources (excluding the Hot Springs) have frozen over completely but large water sources are kept flowing by large dinosaurs\n- I'd like to place blizzards but I don't want to cause massive lag, so you'll have to imagine them."
    }
}

SEASON_ORDER = ["the blooming", "the drought", "the brightening", "the freeze"]
SEASON_LENGTH_DAYS = 14
SEASON_ROTATION_START = datetime(2025, 4, 9, 12, 0, 0)
STATE_FILE = "season_state.json"

async def post_season_announcement(bot, season_key, channel_id, force=False):
    season = season_data[season_key]
    times = get_current_season_times()

    # Check last announced state
    last_announced = None
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
            last_announced = state.get("last_season")

    if not force and last_announced == season_key:
        print("✅ Season already announced — skipping repeat.")
        return

    channel = bot.get_channel(channel_id)
    if not channel:
        print("Channel not found")
        return

    async for msg in channel.history(limit=2):
        await msg.delete()

    try:
        emoji = season.get("emoji", "🌿")
        await channel.edit(name=f"{emoji}season{emoji}")
    except Exception as e:
        print(f"Failed to rename channel: {e}")

    banner_file = discord.File(season["banner"], filename=season["banner"])
    await channel.send(file=banner_file)

    embed = discord.Embed(
        title=season_key.title(),
        description=season["description"],
        color=0x87cefa
    )
    embed.add_field(name="This season started:", value=f"<t:{int(times['start_time'].timestamp())}:F>", inline=True)
    embed.add_field(name="This season will end:", value=f"<t:{int(times['end_time'].timestamp())}:F>", inline=True)
    await channel.send(embed=embed)

    # Post short version to announcement channel
    announce_channel = bot.get_channel(1303378387947229225)
    if announce_channel:
        short_embed = discord.Embed(description=season["announcement"], color=0xf1c40f)
        short_embed.set_footer(text="Follow this channel to receive seasonal updates in your own server!")
        announce_msg = await announce_channel.send(embed=short_embed)
        try:
            await announce_msg.publish()
        except Exception as e:
            print(f"Failed to publish announcement: {e}")

    with open(STATE_FILE, "w") as f:
        json.dump({"last_season": season_key}, f)

def get_current_season():
    now = datetime.now()
    days_since_start = (now - SEASON_ROTATION_START).days
    index = (days_since_start // SEASON_LENGTH_DAYS) % len(SEASON_ORDER)
    return SEASON_ORDER[index]

def get_current_season_times():
    now = datetime.now()
    days_since_start = (now - SEASON_ROTATION_START).days
    cycles_since_start = days_since_start // SEASON_LENGTH_DAYS
    current_start = SEASON_ROTATION_START + timedelta(days=cycles_since_start * SEASON_LENGTH_DAYS)
    current_end = current_start + timedelta(days=SEASON_LENGTH_DAYS)
    return {"start_time": current_start, "end_time": current_end}
