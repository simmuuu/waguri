import os
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands


class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="sync")
    async def sync(
        self, interaction: discord.Interaction, mode: Literal["tree", "cogs"]
    ):
        if not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message(
                "you are not the owner of this bot >:(", ephemeral=True
            )

        match mode:
            case "tree":
                await self._sync_tree(interaction)
            case "cogs":
                await self._sync_cogs(interaction)

    async def _sync_tree(self, interaction: discord.Interaction):
        guild = discord.Object(id=os.environ["GUILD_ID"])

        self.bot.tree.copy_global_to(guild=guild)
        synced = await self.bot.tree.sync(guild=guild)
        await interaction.response.send_message(
            f"{len(synced)} app commands synced!", ephemeral=True
        )

    async def _sync_cogs(self, interaction: discord.Interaction):
        loaded = set(self.bot.extensions.keys())
        on_disk = {
            f"cogs.{f[:-3]}"
            for f in os.listdir("./cogs")
            if f.endswith(".py")
            if not f.startswith("_")
        }

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
