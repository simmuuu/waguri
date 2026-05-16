import os

from dotenv import load_dotenv

from bot import WaguriBot

load_dotenv()

bot = WaguriBot()
bot.run(os.environ["DISCORD_TOKEN"])
