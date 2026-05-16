import os

import discord
from discord.ext import commands


class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, mode: str | None):
        match mode:
            case "tree":
                await self._sync_tree(ctx)
            case "cogs":
                await self._sync_cogs(ctx)
            case _:
                await ctx.send("Usage: !sync <tree|cogs>")

    async def _sync_tree(self, ctx: commands.Context):
        guild = discord.Object(id=os.environ["GUILD_ID"])

        self.bot.tree.copy_global_to(guild=guild)
        synced = await self.bot.tree.sync(guild=guild)
        await ctx.send(f"{len(synced)} app commands synced!")

    async def _sync_cogs(self, ctx: commands.Context):
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

        await ctx.send("\n".join(results))


async def setup(bot: commands.Bot):
    await bot.add_cog(Dev(bot))
