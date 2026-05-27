import json

from mcp.server.fastmcp import FastMCP

from src.tools import redis_client as rd


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def redis_get(key: str) -> str:
        """Get the value of a Redis key."""
        val = await rd.get(key)
        return val if val is not None else f"Key '{key}' not found."

    @mcp.tool()
    async def redis_keys(pattern: str = "*") -> str:
        """List Redis keys matching a glob pattern (default: *)."""
        keys = await rd.keys(pattern)
        return json.dumps(keys, indent=2) if keys else "No keys found."
