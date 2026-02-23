import redis.asyncio as redis


class RedisClient:
    """Async Redis client."""

    def __init__(self, url: str):
        self._url = url
        self._client: redis.Redis | None = None

    def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(self._url, decode_responses=True)
        return self._client

    async def get(self, key: str) -> str | None:
        return await self._get_client().get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        return await self._get_client().set(key, value, ex=ex)

    async def delete(self, *keys: str) -> int:
        return await self._get_client().delete(*keys)

    async def keys(self, pattern: str = "*") -> list[str]:
        return await self._get_client().keys(pattern)

    async def close(self):
        if self._client:
            await self._client.aclose()
