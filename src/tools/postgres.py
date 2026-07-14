import json

from mcp.server.fastmcp import FastMCP

from src.tools import resolve_postgres_client


def _serialize(rows: list[dict]) -> str:
    return json.dumps(rows, default=str, indent=2)


def _db_name(db: str) -> str | None:
    """Empty string means use the host's default database."""
    return db.strip() or None


def _client(host: str, environment: str):
    return resolve_postgres_client(host, environment)


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def pg_query(sql: str, host: str, environment: str, db: str = "") -> str:
        """Run a read-only SQL query against PostgreSQL and return results as JSON.

        Credentials are configured server-side per host/environment and never
        passed by the caller.

        Args:
            sql: SQL query to run (read-only).
            host: Target PostgreSQL host/cluster (e.g. microservices, merchant, openapipartner).
            environment: Target environment (dev, qa, uat, prod).
            db: Database name on that host. Leave empty to use the host's default database.
        """
        rows = await _client(host, environment).fetch(_db_name(db), sql)
        return _serialize(rows) or "No rows returned."

    @mcp.tool()
    async def pg_list_tables(host: str, environment: str, schema: str = "public", db: str = "") -> str:
        """List all tables in a PostgreSQL schema.

        Args:
            host: Target PostgreSQL host/cluster (e.g. microservices, merchant, openapipartner).
            environment: Target environment (dev, qa, uat, prod).
            schema: Schema name (default: public).
            db: Database name on that host. Leave empty to use the host's default database.
        """
        rows = await _client(host, environment).fetch(
            _db_name(db),
            "SELECT table_name FROM information_schema.tables WHERE table_schema = $1 ORDER BY table_name",
            schema,
        )
        return "\n".join(r["table_name"] for r in rows) or "No tables found."

    @mcp.tool()
    async def pg_describe_table(
        table_name: str, host: str, environment: str, schema: str = "public", db: str = ""
    ) -> str:
        """Describe columns of a PostgreSQL table (name, type, nullable, default).

        Args:
            table_name: Table name.
            host: Target PostgreSQL host/cluster (e.g. microservices, merchant, openapipartner).
            environment: Target environment (dev, qa, uat, prod).
            schema: Schema name (default: public).
            db: Database name on that host. Leave empty to use the host's default database.
        """
        rows = await _client(host, environment).fetch(
            _db_name(db),
            "SELECT column_name, data_type, is_nullable, column_default "
            "FROM information_schema.columns WHERE table_schema = $1 AND table_name = $2 "
            "ORDER BY ordinal_position",
            schema,
            table_name,
        )
        return _serialize(rows) or f"Table '{schema}.{table_name}' not found."

    @mcp.tool()
    async def pg_list_indexes(
        table_name: str, host: str, environment: str, schema: str = "public", db: str = ""
    ) -> str:
        """List indexes on a PostgreSQL table.

        Args:
            table_name: Table name.
            host: Target PostgreSQL host/cluster (e.g. microservices, merchant, openapipartner).
            environment: Target environment (dev, qa, uat, prod).
            schema: Schema name (default: public).
            db: Database name on that host. Leave empty to use the host's default database.
        """
        rows = await _client(host, environment).fetch(
            _db_name(db),
            "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = $1 AND tablename = $2 ORDER BY indexname",
            schema,
            table_name,
        )
        return _serialize(rows) or f"No indexes found for '{schema}.{table_name}'."
