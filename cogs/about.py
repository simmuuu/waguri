import os

import discord
from discord import app_commands
from discord.ext import commands

GITHUB_USERNAME = "simmuuu"
GITHUB_REPO_URL = "https://github.com/simmuuu/waguri"
CODEBERG_REPO_URL = "https://codeberg.org/simmu/waguri"
AVATAR_URL = f"https://github.com/{GITHUB_USERNAME}.png"


class About(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="about")
    async def about(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="about",
            description=(
                "a simple discord bot.\n\n"
                f"[Github]({GITHUB_REPO_URL}) | [Codeberg]({CODEBERG_REPO_URL})"
            ),
        )
        embed.set_thumbnail(url=AVATAR_URL)

        commit_hash = os.getenv("COMMIT_SHA")
        short = commit_hash[:7] if commit_hash is not None else "unknown"

        embed.set_footer(text=f"Commit SHA: {short}")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(About(bot))
