import json

from mcp.server.fastmcp import FastMCP

from src.tools import redis_clients, resolve_client


def _client(environment: str):
    return resolve_client(redis_clients, environment, "redis")


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def redis_get(key: str, environment: str) -> str:
        """Get the value of a Redis key.

        Args:
            key: Redis key to fetch.
            environment: Target environment (dev, qa, uat, prod).
        """
        val = await _client(environment).get(key)
        return val if val is not None else f"Key '{key}' not found."

    @mcp.tool()
    async def redis_keys(environment: str, pattern: str = "*") -> str:
        """List Redis keys matching a glob pattern (default: *).

        Args:
            environment: Target environment (dev, qa, uat, prod).
            pattern: Glob pattern to match keys against (default: *).
        """
        keys = await _client(environment).keys(pattern)
        return json.dumps(keys, indent=2) if keys else "No keys found."
