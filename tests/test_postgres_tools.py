import pytest
from unittest.mock import AsyncMock, patch

from tests.conftest import load_tool_functions

_tools = load_tool_functions("src.tools.postgres")
pg_query = _tools["pg_query"]
pg_list_tables = _tools["pg_list_tables"]
pg_describe_table = _tools["pg_describe_table"]
pg_list_indexes = _tools["pg_list_indexes"]


def _patched(mock_pg, host="microservices", environment="uat"):
    return patch("src.tools.postgres_clients", {(host, environment): mock_pg})


@pytest.mark.asyncio
async def test_pg_query_with_results():
    mock_pg = AsyncMock()
    mock_pg.fetch.return_value = [{"id": 1, "name": "John"}]
    with _patched(mock_pg):
        result = await pg_query(sql="SELECT * FROM users", host="microservices", environment="uat")
    assert '"id": 1' in result
    assert '"name": "John"' in result
    mock_pg.fetch.assert_called_once_with(None, "SELECT * FROM users")


@pytest.mark.asyncio
async def test_pg_query_with_db():
    mock_pg = AsyncMock()
    mock_pg.fetch.return_value = [{"id": 1}]
    with _patched(mock_pg):
        result = await pg_query(sql="SELECT 1", host="microservices", environment="uat", db="order_engine")
    assert '"id": 1' in result
    mock_pg.fetch.assert_called_once_with("order_engine", "SELECT 1")


@pytest.mark.asyncio
async def test_pg_query_no_results():
    mock_pg = AsyncMock()
    mock_pg.fetch.return_value = []
    with _patched(mock_pg):
        result = await pg_query(sql="SELECT * FROM empty", host="microservices", environment="uat")
    assert result == "[]"


@pytest.mark.asyncio
async def test_pg_query_unknown_host_environment():
    with patch("src.tools.postgres_clients", {}):
        with pytest.raises(
            ValueError,
            match="No postgres client configured for host 'merchant' and environment 'dev'",
        ):
            await pg_query(sql="SELECT 1", host="merchant", environment="dev")


@pytest.mark.asyncio
async def test_pg_query_wrong_environment_for_host():
    mock_pg = AsyncMock()
    with _patched(mock_pg, host="microservices", environment="uat"):
        with pytest.raises(
            ValueError,
            match="No postgres client configured for host 'microservices' and environment 'prod'",
        ):
            await pg_query(sql="SELECT 1", host="microservices", environment="prod")


@pytest.mark.asyncio
async def test_pg_list_tables_with_results():
    mock_pg = AsyncMock()
    mock_pg.fetch.return_value = [{"table_name": "users"}, {"table_name": "orders"}]
    with _patched(mock_pg):
        result = await pg_list_tables(host="microservices", environment="uat")
    assert result == "users\norders"


@pytest.mark.asyncio
async def test_pg_list_tables_no_results():
    mock_pg = AsyncMock()
    mock_pg.fetch.return_value = []
    with _patched(mock_pg):
        result = await pg_list_tables(host="microservices", environment="uat")
    assert result == "No tables found."


@pytest.mark.asyncio
async def test_pg_describe_table_with_results():
    mock_pg = AsyncMock()
    mock_pg.fetch.return_value = [{"column_name": "id", "data_type": "integer", "is_nullable": "NO", "column_default": None}]
    with _patched(mock_pg):
        result = await pg_describe_table(table_name="users", host="microservices", environment="uat")
    assert '"column_name": "id"' in result


@pytest.mark.asyncio
async def test_pg_describe_table_not_found():
    mock_pg = AsyncMock()
    mock_pg.fetch.return_value = []
    with _patched(mock_pg):
        result = await pg_describe_table(
            table_name="nonexistent", host="microservices", environment="uat", schema="test"
        )
    assert result == "[]"  # _serialize([]) is truthy, so fallback doesn't trigger


@pytest.mark.asyncio
async def test_pg_list_indexes_with_results():
    mock_pg = AsyncMock()
    mock_pg.fetch.return_value = [{"indexname": "users_pkey", "indexdef": "CREATE UNIQUE INDEX ..."}]
    with _patched(mock_pg):
        result = await pg_list_indexes(table_name="users", host="microservices", environment="uat")
    assert '"indexname": "users_pkey"' in result


@pytest.mark.asyncio
async def test_pg_list_indexes_no_results():
    mock_pg = AsyncMock()
    mock_pg.fetch.return_value = []
    with _patched(mock_pg):
        result = await pg_list_indexes(table_name="t", host="microservices", environment="uat", schema="s")
    assert result == "[]"
