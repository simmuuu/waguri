import discord
from discord import app_commands
from discord.ext import commands

from bot import WaguriBot


# https://github.com/ni5arga/discord-bot/blob/main/modules/url_shortener.py
class URL_Shortener(commands.Cog):
    def __init__(self, bot: WaguriBot):
        self.bot = bot
        self.tinyurl_api = "http://tinyurl.com/api-create.php?url="

    @app_commands.command(name="url_shorten", description="TinyURL Shortener")
    async def url_shorten(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()

        resp = await self.bot.http_client.get(self.tinyurl_api + url)

        if not resp.ok:
            await interaction.followup.send("Failed to shorten URL.")
            return

        await interaction.followup.send(resp.data, suppress_embeds=True)


async def setup(bot: WaguriBot):
    await bot.add_cog(URL_Shortener(bot))
