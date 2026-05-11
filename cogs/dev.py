import os

import discord
from discord import app_commands
from discord.ext import commands


class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="sync_cogs", description="sync cogs !!! DEV MODE ONLY !!!"
    )
    @commands.is_owner()
    async def sync_cogs(self, interaction: discord.Interaction):
        loaded = set(self.bot.extensions.keys())
        on_disk = {f"cogs.{f[:-3]}" for f in os.listdir("./cogs") if f.endswith(".py")}

        to_load = on_disk - loaded
        to_unload = loaded - on_disk
        to_reload = on_disk & loaded

        results = []

        for ext in to_unload:
            try:
                await self.bot.unload_extension(ext)
                results.append(f"unloaded {ext}")
            except Exception as e:
                results.append(f"{ext}: {e}")

        for ext in to_load:
            try:
                await self.bot.load_extension(ext)
                results.append(f"loaded {ext}")
            except Exception as e:
                results.append(f"{ext}: {e}")

        for ext in to_reload:
            try:
                await self.bot.reload_extension(ext)
                results.append(f"reloaded {ext}")
            except Exception as e:
                results.append(f"{ext}: {e}")

        await interaction.response.send_message("\n".join(results), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Dev(bot))
