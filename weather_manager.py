#weather_manager.py
class WeatherManager:
    def __init__(self, bot):
        self.bot = bot
        self.paused = False

    async def start_weather_loop(self):
        # Loop every 20 mins to pick and apply weather unless paused
        pass

    def pause_weather(self):
        self.paused = True

    def resume_weather(self):
        self.paused = False

    async def update_weather(self):
        # Apply weather via RCON and post Discord message
        pass
