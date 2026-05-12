import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def setup_hook():
    is_dev = "waguri_dev" in os.environ

    for filename in os.listdir("./cogs"):
        if not filename.endswith(".py"):
            continue

        file = filename[:-3]

        if file == "dev" and not is_dev:
            continue

        await bot.load_extension(f"cogs.{file}")

    # sync application commands
    if "waguri_prod" in os.environ:
        await bot.tree.sync()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


load_dotenv()
# bot.run will raise KeyError if env variable is missing
bot.run(os.environ["DISCORD_TOKEN"])
