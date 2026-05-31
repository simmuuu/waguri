import asyncio
import base64
import io
import socket
from collections import defaultdict

import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands, tasks
from mcstatus import JavaServer
from mcstatus.responses.java import JavaStatusResponse

from bot import WaguriBot
from db.minecraft import (
    delete_monitor,
    init_db,
    insert_ignore_player,
    load_ignore_players,
    load_monitors,
    remove_ignore_player,
    save_monitor,
)
from models.minecraft import LatencyTier, MonitoredServer, ServerState

STATUS_TIMEOUT = 5.0
QUERY_TIMEOUT = 8.0


class Minecraft(commands.Cog):
    def __init__(self, bot: WaguriBot):
        self.bot = bot
        self.db: aiosqlite.Connection = self.bot.db.connection
        self._monitors: dict[int, MonitoredServer] = {}
        self._ignore_players: dict[int, set[str]] = defaultdict(set)

    async def cog_load(self) -> None:
        await init_db(self.db)
        self._monitors = await load_monitors(self.db)
        self._ignore_players = await load_ignore_players(self.db)
        self._poll_loop.start()

    async def cog_unload(self) -> None:
        self._poll_loop.cancel()

    # ---------------------------------------------
    # Commands
    # ---------------------------------------------

    minecraft = app_commands.Group(name="minecraft", description="Minecraft Commands")

    @minecraft.command(name="info", description="Minecraft Server Info")
    @app_commands.describe(port="Default: 25565", query_port="Default: 25565")
    async def info(
        self,
        interaction: discord.Interaction,
        address: str | None = None,
        port: int = 25565,
        query_port: int = 25565,
    ):
        if interaction.guild_id is None or interaction.channel_id is None:
            await interaction.response.send_message(
                "This command must be used in a server.", ephemeral=True
            )
            return

        if not address and interaction.channel_id in self._monitors:
            ms = self._monitors[interaction.channel_id]
            address, port, query_port = ms.address, ms.port, ms.query_port

        if not address:
            await interaction.response.send_message(
                "This channel is not being monitored. Please either add monitoring or provide an address.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        try:
            _, status, players, query_ok = await self._fetch_server_data(
                address, port, query_port
            )
        except TimeoutError:
            await interaction.followup.send(
                embed=discord.Embed(
                    description=f"Server did not respond within {STATUS_TIMEOUT:.0f}s.",
                    color=0xED4245,
                )
            )
            return
        except socket.gaierror:
            await interaction.followup.send(
                embed=discord.Embed(
                    description="Could not resolve server address.",
                    color=0xED4245,
                )
            )
            return
        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(description=f"Error: {e}", color=0xED4245)
            )
            return

        embed, file = self._build_status_embed(status, players, query_ok)
        if file:
            await interaction.followup.send(embed=embed, file=file)
        else:
            await interaction.followup.send(embed=embed)

    @minecraft.command(
        name="monitor",
        description="Start monitoring a server and posting alerts to this channel",
    )
    @app_commands.describe(
        address="Server address",
        port="Default: 25565",
        query_port="Default: 25565",
        interval="Poll interval in seconds (min 30, max 300, default 60)",
    )
    @app_commands.guild_only()
    async def monitor(
        self,
        interaction: discord.Interaction,
        address: str,
        port: int = 25565,
        query_port: int = 25565,
        interval: app_commands.Range[int, 30, 300] = 60,
    ):
        if interaction.guild_id is None or interaction.channel_id is None:
            await interaction.response.send_message(
                "This command must be used in a server.", ephemeral=True
            )
            return

        ms = MonitoredServer(
            guild_id=interaction.guild_id,
            channel_id=interaction.channel_id,
            address=address,
            port=port,
            query_port=query_port,
            interval=interval,
        )

        self._monitors[interaction.channel_id] = ms
        await save_monitor(self.db, ms)

        await interaction.response.send_message(
            f"Now monitoring **{address}** - alerts in this channel (polling every {interval}s).",
            ephemeral=True,
        )

    @minecraft.command(
        name="unmonitor",
        description="Stop monitoring the server",
    )
    @app_commands.guild_only()
    async def unmonitor(self, interaction: discord.Interaction):
        if interaction.guild_id is None or interaction.channel_id is None:
            await interaction.response.send_message(
                "This command must be used in a server.", ephemeral=True
            )
            return

        ms = self._monitors.pop(interaction.channel_id, None)
        await delete_monitor(self.db, interaction.channel_id)

        msg = (
            f"Monitoring stopped. ({ms.address})"
            if ms
            else "No server is being monitored here."
        )
        await interaction.response.send_message(msg, ephemeral=True)

    @minecraft.command(name="ignore", description="Toggle player ignore event")
    async def ignore(self, interaction: discord.Interaction, username: str):
        if interaction.guild_id is None or interaction.channel_id is None:
            await interaction.response.send_message(
                "This command must be used in a server.", ephemeral=True
            )
            return

        channel_id = interaction.channel_id
        ignored = self._ignore_players[channel_id]

        if username in ignored:
            await remove_ignore_player(self.db, channel_id, username)
            ignored.discard(username)
            await interaction.response.send_message(
                f"**{username}** will no longer be ignored (by {interaction.user.mention}).\nRun the command again to ignore player events."
            )
        else:
            await insert_ignore_player(self.db, channel_id, username)
            ignored.add(username)
            await interaction.response.send_message(
                f"**{username}** has been ignored.\nRun the command again to stop ignoring player events.",
                ephemeral=True,
            )

    # ---------------------------------------------
    # Poll Loop Stuff
    # ---------------------------------------------
    @tasks.loop(seconds=10)
    async def _poll_loop(self):
        now = asyncio.get_running_loop().time()
        for ms in list(self._monitors.values()):
            if ms._polling:
                continue
            if now - ms._last_poll < ms.effective_interval:
                continue
            ms._last_poll = now
            ms._polling = True
            asyncio.create_task(self._poll_server(ms))

    @_poll_loop.before_loop
    async def _before_poll(self):
        await self.bot.wait_until_ready()

    async def _poll_server(self, ms: MonitoredServer) -> None:
        try:
            await self._do_poll(ms)
        finally:
            ms._polling = False

    async def _do_poll(self, ms: MonitoredServer) -> None:
        channel = self.bot.get_channel(ms.channel_id)
        if channel is None:
            return

        if not isinstance(channel, discord.abc.Messageable):
            return

        try:
            _, status, current_players, query_ok = await self._fetch_server_data(
                ms.address, ms.port, ms.query_port
            )
            ms._status_fails = 0
            current_players -= self._ignore_players.get(ms.channel_id, set())
        except Exception:
            # transition to offline
            ms._status_fails += 1
            if ms._status_fails > ms.STATUS_FAIL_THRESHOLD:
                await self._transition(ms, ServerState.OFFLINE, channel, status=None)
            return

        if not query_ok:
            ms._query_fails += 1
        else:
            ms._query_fails = 0

        curr_state = (
            ServerState.DEGRADED
            if ms._query_fails >= ms.QUERY_FAIL_THRESHOLD
            else ServerState.ONLINE
        )
        # transition to degraded/online based upon query fails
        await self._transition(ms, curr_state, channel, status=status)
        await self._check_latency(ms, status.latency, channel)

        if query_ok and ms.state == ServerState.ONLINE:
            joined = current_players - ms.players_online
            left = ms.players_online - current_players

            if joined:
                names = ", ".join(f"**{p}**" for p in sorted(joined))
                await channel.send(f"🟢 {names} joined **{ms.address}**")
            if left:
                names = ", ".join(f"**{p}**" for p in sorted(left))
                await channel.send(f"🔴 {names} left **{ms.address}**")
            ms.players_online = current_players

    # ---------------------------------------------
    # State Handlers
    # ---------------------------------------------

    async def _transition(
        self,
        ms: MonitoredServer,
        new_state: ServerState,
        channel: discord.abc.Messageable,
        *,
        status: JavaStatusResponse | None,
    ):
        """
        State Transition function which also sends a discord embed.
        """
        if new_state == ms.state:
            return
        old_state = ms.state
        ms.state = new_state
        addr = ms.address

        if new_state == ServerState.ONLINE:
            color, title = 0x57F287, "Server online"
            desc = f"**{addr}** is back online."
            if status:
                desc += (
                    f"\nPlayers: {status.players.online}/{status.players.max}"
                    f"\nPing: {round(status.latency, 2)}ms"
                )
        elif new_state == ServerState.DEGRADED:
            color, title = 0xFEE75C, "Query Port Not Responding"
            desc = (
                f"**{addr}** is reachable but query is not responding.\n"
                "Player list tracking paused."
            )
        elif new_state == ServerState.OFFLINE:
            color, title = 0xED4245, "Server offline"
            desc = (
                f"**{addr}** is not responding.\n"
                f"Next check in {ms.effective_interval:.0f}s."
            )
        else:
            color, title = 0x99AAB5, "Status unknown"
            desc = f"**{addr}** status is unknown."
        embed = discord.Embed(title=title, description=desc, color=color)
        embed.set_footer(text=f"{old_state.name.lower()} → {new_state.name.lower()}")
        await channel.send(embed=embed)

    async def _check_latency(
        self, ms: MonitoredServer, latency: float, channel: discord.abc.Messageable
    ):
        tier = LatencyTier.classify(latency)
        if tier == ms._latency_tier:
            return
        ms._latency_tier = tier
        await channel.send(
            embed=discord.Embed(
                description=f"**{tier.format(latency)}** - {ms.address}",
                color=tier.color,
            )
        )

    # ---------------------------------------------
    # Helpers
    # ---------------------------------------------

    async def _fetch_server_data(
        self, address: str, port: int, query_port: int
    ) -> tuple[JavaServer, JavaStatusResponse, set, bool]:
        async with asyncio.timeout(STATUS_TIMEOUT):
            ip = await self._get_ip_address(address)
            server = JavaServer(host=ip, port=port, query_port=query_port)
            status = await server.async_status()

        try:
            async with asyncio.timeout(QUERY_TIMEOUT):
                query = await server.async_query()
                players = set(query.players.list or [])
                query_ok = True
        except Exception:
            players = set()
            query_ok = False

        return server, status, players, query_ok

    def _build_status_embed(
        self, status: JavaStatusResponse, players: set, query_ok: bool
    ) -> tuple[discord.Embed, discord.File | None]:
        name = status.motd.to_plain().strip()
        embed = discord.Embed(title=name, color=0x5B8731)
        embed.add_field(name="Ping", value=f"{round(status.latency, 2)}ms")
        embed.add_field(
            name="Online", value=f"{status.players.online}/{status.players.max}"
        )

        if query_ok and players:
            embed.add_field(
                name="Players",
                value=f"```\n{'\n'.join(sorted(players))}\n```",
                inline=False,
            )
        elif not query_ok:
            embed.add_field(
                name="Players", value="*Query port unavailable*", inline=False
            )

        embed.set_footer(text=f"Version: {status.version.name}")

        if status.icon:
            _, b64 = status.icon.split(",")
            buf = io.BytesIO(base64.b64decode(b64))
            file = discord.File(buf, filename="server_icon.png")
            embed.set_thumbnail(url="attachment://server_icon.png")
            return embed, file

        return embed, None

    async def _get_ip_address(self, address: str) -> str:
        loop = asyncio.get_running_loop()

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


async def setup(bot: WaguriBot):
    await bot.add_cog(Minecraft(bot))
