import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.command()
async def hello(ctx: commands.Context):
    await ctx.send(f"Hello {ctx.author.name}")


@bot.command()
async def add(ctx: commands.Context, a: int, b: int):
    await ctx.send(f"{a} + {b} = {a + b}")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


load_dotenv()

# bot.run will raise KeyError if env variable is missing
bot.run(os.environ["DISCORD_TOKEN"])
