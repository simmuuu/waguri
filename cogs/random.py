import random

import discord
from discord import app_commands
from discord.ext import commands


class Random(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="coin_flip", description="Flip a Coin")
    async def coin_flip(self, interaction: discord.Interaction):
        await interaction.response.send_message(random.choice(["Heads!", "Tails!"]))

    @app_commands.command(name="dice_roll", description="Roll a Dice")
    @app_commands.describe(max="Default: 6")
    async def dice_roll(self, interaction: discord.Interaction, max: int = 6):
        await interaction.response.send_message(random.randint(1, max))


async def setup(bot: commands.Bot):
    await bot.add_cog(Random(bot))
