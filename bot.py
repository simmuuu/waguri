import os
import pathlib

import discord
from discord.ext import commands

from db.database import Database
from utils.http import HttpClient

BASE_PATH = pathlib.Path(__file__).resolve().parent
COGS_DIR = BASE_PATH / "cogs"

intents = discord.Intents.default()
intents.message_content = True


class WaguriBot(commands.Bot):
    http_client: HttpClient

    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.db = Database()
        self.http_client = HttpClient()

    async def setup_hook(self):
        await self.db.setup()
        self.http_client.start()
        await self._load_cogs()

    async def _load_cogs(self):
        is_dev = "waguri_dev" in os.environ

        for p in COGS_DIR.iterdir():
            if not p.suffix == ".py":
                continue
            if p.stem.startswith("_"):
                continue
            if p.stem == "dev" and not is_dev:
                continue
            await self.load_extension(f"cogs.{p.stem}")

        # sync application commands
        if "waguri_prod" in os.environ:
            await self.tree.sync()

    async def close(self) -> None:
        await super().close()
        await self.db.close()
        await self.http_client.close()

    async def on_ready(self):
        print(f"Logged in as {self.user}", flush=True)
