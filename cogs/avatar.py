import discord
from discord import app_commands
from discord.ext import commands


class Avatar(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="avatar", description="Get a Users Avatar")
    @app_commands.guild_only()
    async def avatar(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
    ):
        user = user
        if not user.avatar:
            await interaction.response.send_message("No avatar set.", ephemeral=True)
            return

        embed = discord.Embed(title=f"{user.name}'s avatar", color=user.color)
        embed.set_image(url=user.avatar.url)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Avatar(bot))
