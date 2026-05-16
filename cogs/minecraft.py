import asyncio
import base64
import io
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
            ip_addr = await self.get_ip_address(address)
            server = JavaServer(host=ip_addr, port=port, query_port=query_port)
            status = await server.async_status()

            players_online, players_max = status.players.online, status.players.max
            ping = round(status.latency, 2)
            name = status.motd.to_plain().strip()
            player_list = ""

            try:
                query = await server.async_query()
                if query.players.list:
                    player_list = "\n".join(query.players.list)
            except Exception:
                player_list = "Couldn't retrieve player list."

            embed = discord.Embed(title=name, color=0x5B8731)
            embed.add_field(name="Ping", value=f"{ping}ms")
            embed.add_field(name="Online", value=f"{players_online}/{players_max}")

            if player_list:
                embed.add_field(
                    name="Players", value=f"```\n{player_list}\n```", inline=False
                )

            if status.icon:
                _, base64_data = status.icon.split(",")
                image_bytes = base64.b64decode(base64_data)
                buffer = io.BytesIO(image_bytes)
                file = discord.File(buffer, filename="server_icon.png")
                embed.set_thumbnail(url="attachment://server_icon.png")
                await interaction.followup.send(embed=embed, file=file)
            else:
                await interaction.followup.send(embed=embed)
        except socket.gaierror:
            await interaction.followup.send("Could not resolve server address.")
        except Exception as e:
            await interaction.followup.send(f"Error: {e}")

    # consider aiodns
    async def get_ip_address(self, address: str):
        loop = asyncio.get_event_loop()
        resolved_ip = ""

        # Try IPv6 first
        try:
            infos = await loop.run_in_executor(
                None, lambda: socket.getaddrinfo(address, 25565, socket.AF_INET6)
            )
            resolved_ip = str(infos[0][4][0])
        # else IPv4
        except socket.gaierror:
            infos = await loop.run_in_executor(
                None, lambda: socket.getaddrinfo(address, 25565, socket.AF_INET)
            )
            resolved_ip = str(infos[0][4][0])

        return resolved_ip


async def setup(bot: commands.Bot):
    await bot.add_cog(Minecraft(bot))
