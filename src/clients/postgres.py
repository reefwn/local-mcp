import asyncpg
from urllib.parse import urlparse


class PostgresClient:
    """Async PostgreSQL client using asyncpg with fixed connection params."""

    def __init__(self, url: str):
        parsed = urlparse(url)
        self._host = parsed.hostname
        self._port = parsed.port or 5432
        self._user = parsed.username
        self._password = parsed.password
        self._default_database = parsed.path.lstrip('/') if parsed.path else 'postgres'
        self._pools: dict[str, asyncpg.Pool] = {}

    async def _get_pool(self, database: str | None = None) -> asyncpg.Pool:
        db = database or self._default_database
        if db not in self._pools:
            self._pools[db] = await asyncpg.create_pool(
                host=self._host,
                port=self._port,
                user=self._user,
                password=self._password,
                database=db,
                min_size=1,
                max_size=5
            )
        return self._pools[db]

    async def fetch(self, database: str | None = None, query: str = "", *args) -> list[dict]:
        pool = await self._get_pool(database)
        rows = await pool.fetch(query, *args)
        return [dict(r) for r in rows]

    async def execute(self, database: str | None = None, query: str = "", *args) -> str:
        pool = await self._get_pool(database)
        return await pool.execute(query, *args)

    async def close(self):
        for pool in self._pools.values():
            await pool.close()
