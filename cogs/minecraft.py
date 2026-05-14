import asyncio
import socket

import discord
from discord import app_commands
from discord.ext import commands
from mcstatus import JavaServer


class Minecraft(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="mc_info", description="minecraft server info")
    @app_commands.describe(port="default: 25565", query_port="default: 25565")
    async def mc_info(
        self,
        interaction: discord.Interaction,
        address: str,
        port: int = 25565,
        query_port: int = 25565,
    ):
        await interaction.response.defer()
        try:
            loop = asyncio.get_event_loop()
            infos = await loop.run_in_executor(
                None, lambda: socket.getaddrinfo(address, port, socket.AF_INET6)
            )
            ipv6_address = str(infos[0][4][0])

            server = JavaServer(host=ipv6_address, port=port, query_port=query_port)
            status = await server.async_status()

            players_online, players_max = status.players.online, status.players.max
            ping = round(status.latency, 2)

            player_list = ""
            try:
                query = await server.async_query()
                if query.players.list:
                    player_list = f"\nPlayers: {', '.join(query.players.list)}"
            except Exception:
                player_list = "\nFailed to interact with query port."

            await interaction.followup.send(
                f"Ping: {ping}ms\nOnline: {players_online}/{players_max}\n{player_list}"
            )
        except Exception as e:
            await interaction.followup.send(f"Error: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Minecraft(bot))
