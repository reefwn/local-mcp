import asyncio

from mcp.server.fastmcp import FastMCP

from src.tools import config

# Port assignments per client group
PORTS = {
    "atlassian": 7373,
    "postgres": 7374,
    "redis": 7375,
    "kafka": 7376,
    "figma": 7377,
    "obsidian": 7378,
    "elasticsearch": 7379,
}


def _make_server(name: str) -> FastMCP:
    return FastMCP(f"local-mcp-{name}", host="0.0.0.0", port=PORTS[name])


async def main() -> None:
    servers: list[FastMCP] = []

    if config.enable_jira or config.enable_confluence or config.enable_bitbucket:
        mcp = _make_server("atlassian")
        if config.enable_jira:
            from src.tools import jira
            jira.register(mcp)
        if config.enable_confluence:
            from src.tools import confluence
            confluence.register(mcp)
        if config.enable_bitbucket:
            from src.tools import bitbucket
            bitbucket.register(mcp)
        servers.append(mcp)

    if config.enable_postgres:
        mcp = _make_server("postgres")
        from src.tools import postgres
        postgres.register(mcp)
        servers.append(mcp)

    if config.enable_redis:
        mcp = _make_server("redis")
        from src.tools import redis
        redis.register(mcp)
        servers.append(mcp)

    if config.enable_kafka:
        mcp = _make_server("kafka")
        from src.tools import kafka
        kafka.register(mcp)
        servers.append(mcp)

    if config.enable_figma:
        mcp = _make_server("figma")
        from src.tools import figma
        figma.register(mcp)
        servers.append(mcp)

    if config.enable_obsidian:
        mcp = _make_server("obsidian")
        from src.tools import obsidian
        obsidian.register(mcp)
        servers.append(mcp)

    if config.enable_elasticsearch:
        mcp = _make_server("elasticsearch")
        from src.tools import elasticsearch, apm
        elasticsearch.register(mcp)
        apm.register(mcp)
        servers.append(mcp)

    if not servers:
        print("No clients enabled. Set at least one ENABLE_* env var to true.")
        return

    await asyncio.gather(*[s.run_streamable_http_async() for s in servers])


if __name__ == "__main__":
    asyncio.run(main())
