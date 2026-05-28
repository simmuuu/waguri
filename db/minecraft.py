import aiosqlite

from models.minecraft import MonitoredServer


async def init_db(db: aiosqlite.Connection):
    await db.execute("""
        CREATE TABLE IF NOT EXISTS mc_monitors (
            channel_id INTEGER PRIMARY KEY,
            guild_id   INTEGER NOT NULL,
            address    TEXT NOT NULL,
            port       INTEGER NOT NULL DEFAULT 25565,
            query_port INTEGER NOT NULL DEFAULT 25565,
            interval   INTEGER NOT NULL DEFAULT 60
        )
    """)
    await db.commit()


async def load_monitors(db: aiosqlite.Connection) -> dict[int, MonitoredServer]:
    async with db.execute(
        "SELECT channel_id, guild_id, address, port, query_port, interval FROM mc_monitors"
    ) as cur:
        monitors = []
        for row in await cur.fetchall():
            monitor = MonitoredServer(**dict(row))
            monitors.append(monitor)
        return {monitor.channel_id: monitor for monitor in monitors}


async def save_monitor(db: aiosqlite.Connection, ms: MonitoredServer):
    await db.execute(
        """
        INSERT INTO mc_monitors
        VALUES (:channel_id, :guild_id, :address, :port, :query_port, :interval)
        ON CONFLICT(channel_id) DO UPDATE SET
                    channel_id = excluded.channel_id,
                    address    = excluded.address,
                    port       = excluded.port,
                    query_port = excluded.query_port,
                    interval   = excluded.interval
    """,
        {
            "channel_id": ms.channel_id,
            "guild_id": ms.guild_id,
            "address": ms.address,
            "port": ms.port,
            "query_port": ms.query_port,
            "interval": ms.interval,
        },
    )
    await db.commit()


async def delete_monitor(db: aiosqlite.Connection, channel_id: int):
    await db.execute(
        "DELETE FROM mc_monitors WHERE channel_id = ?",
        (channel_id,),
    )
    await db.commit()
