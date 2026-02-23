import json

from src.clients.redis import RedisClient
from src.tools import config, mcp

rd = RedisClient(config.redis_url)


@mcp.tool()
async def redis_get(key: str) -> str:
    """Get the value of a Redis key."""
    val = await rd.get(key)
    return val if val is not None else f"Key '{key}' not found."


@mcp.tool()
async def redis_set(key: str, value: str, ttl: int | None = None) -> str:
    """Set a Redis key to a value. Optionally set a TTL in seconds."""
    await rd.set(key, value, ex=ttl)
    return f"OK — set '{key}'"


@mcp.tool()
async def redis_delete(key: str) -> str:
    """Delete a Redis key."""
    count = await rd.delete(key)
    return f"Deleted {count} key(s)."


@mcp.tool()
async def redis_keys(pattern: str = "*") -> str:
    """List Redis keys matching a glob pattern (default: *)."""
    keys = await rd.keys(pattern)
    return json.dumps(keys, indent=2) if keys else "No keys found."
