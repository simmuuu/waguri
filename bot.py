import os

import discord
from discord.ext import commands

from utils.http import HttpClient

intents = discord.Intents.default()
intents.message_content = True


class WaguriBot(commands.Bot):
    http_client: HttpClient

    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.http_client = HttpClient()
        self.http_client.start()

        is_dev = "waguri_dev" in os.environ

        for filename in os.listdir("./cogs"):
            if not filename.endswith(".py"):
                continue
            if filename.startswith("_"):
                continue
            file = filename[:-3]
            if file == "dev" and not is_dev:
                continue
            await self.load_extension(f"cogs.{file}")

        # sync application commands
        if "waguri_prod" in os.environ:
            await self.tree.sync()

    async def close(self) -> None:
        await super().close()
        await self.http_client.close()

    async def on_ready(self):
        print(f"Logged in as {self.user}")
