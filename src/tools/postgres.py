import json

from src.tools import config, mcp, postgres_client as pg


def _serialize(rows: list[dict]) -> str:
    return json.dumps(rows, default=str, indent=2)


@mcp.tool()
async def pg_query(database: str | None = None, sql: str = "") -> str:
    """Run a read-only SQL query against PostgreSQL and return results as JSON."""
    rows = await pg.fetch(sql, database=database)
    return _serialize(rows) or "No rows returned."


@mcp.tool()
async def pg_list_tables(database: str | None = None, schema: str = "public") -> str:
    """List all tables in a PostgreSQL schema."""
    rows = await pg.fetch(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = $1 ORDER BY table_name",
        schema,
        database=database,
    )
    return "\n".join(r["table_name"] for r in rows) or "No tables found."


@mcp.tool()
async def pg_describe_table(database: str | None = None, table_name: str = "", schema: str = "public") -> str:
    """Describe columns of a PostgreSQL table (name, type, nullable, default)."""
    rows = await pg.fetch(
        "SELECT column_name, data_type, is_nullable, column_default "
        "FROM information_schema.columns WHERE table_schema = $1 AND table_name = $2 "
        "ORDER BY ordinal_position",
        schema,
        table_name,
        database=database,
    )
    return _serialize(rows) or f"Table '{schema}.{table_name}' not found."


@mcp.tool()
async def pg_list_indexes(database: str | None = None, table_name: str = "", schema: str = "public") -> str:
    """List indexes on a PostgreSQL table."""
    rows = await pg.fetch(
        "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = $1 AND tablename = $2 ORDER BY indexname",
        schema,
        table_name,
        database=database,
    )
    return _serialize(rows) or f"No indexes found for '{schema}.{table_name}'."
