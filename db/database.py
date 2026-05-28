import pathlib

import aiosqlite

BASE_PATH = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = BASE_PATH / "data"
DB_PATH = DATA_DIR / "waguri.db"


class Database:
    def __init__(self) -> None:
        self.db: aiosqlite.Connection | None = None

    async def setup(self):
        if self.db:
            return

        DATA_DIR.mkdir(exist_ok=True)
        self.db = await aiosqlite.connect(DB_PATH)
        self.db.row_factory = aiosqlite.Row
        await self.db.execute("PRAGMA journal_mode=WAL")
        await self.db.execute("PRAGMA foreign_keys=ON")
        await self.db.commit()

    async def close(self):
        if self.db:
            await self.db.close()
            self.db = None

    @property
    def connection(self) -> aiosqlite.Connection:
        if self.db is None:
            raise RuntimeError("Database not initialized")
        return self.db
