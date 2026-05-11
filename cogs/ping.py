from discord.ext import commands


class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context):
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"pong! Latency: {latency}ms")


async def setup(bot: commands.Bot):
    await bot.add_cog(Ping(bot))
