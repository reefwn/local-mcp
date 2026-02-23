import asyncpg


class PostgresClient:
    """Async PostgreSQL client using asyncpg."""

    def __init__(self, url: str):
        self._url = url
        self._pool: asyncpg.Pool | None = None

    async def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self._url, min_size=1, max_size=5)
        return self._pool

    async def fetch(self, query: str, *args) -> list[dict]:
        pool = await self._get_pool()
        rows = await pool.fetch(query, *args)
        return [dict(r) for r in rows]

    async def execute(self, query: str, *args) -> str:
        pool = await self._get_pool()
        return await pool.execute(query, *args)

    async def close(self):
        if self._pool:
            await self._pool.close()
