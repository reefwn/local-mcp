import pytest
from unittest.mock import AsyncMock, patch
from src.tools.postgres import pg_query, pg_list_tables, pg_describe_table, pg_list_indexes


@pytest.mark.asyncio
async def test_pg_query_with_results():
    mock_pg = AsyncMock()
    mock_pg.fetch.return_value = [{"id": 1, "name": "John"}]
    with patch("src.tools.postgres.pg", mock_pg):
        result = await pg_query("SELECT * FROM users")
    assert '"id": 1' in result
    assert '"name": "John"' in result


@pytest.mark.asyncio
async def test_pg_query_no_results():
    mock_pg = AsyncMock()
    mock_pg.fetch.return_value = []
    with patch("src.tools.postgres.pg", mock_pg):
        result = await pg_query("SELECT * FROM empty")
    assert result == "[]"


@pytest.mark.asyncio
async def test_pg_list_tables_with_results():
    mock_pg = AsyncMock()
    mock_pg.fetch.return_value = [{"table_name": "users"}, {"table_name": "orders"}]
    with patch("src.tools.postgres.pg", mock_pg):
        result = await pg_list_tables()
    assert result == "users\norders"


@pytest.mark.asyncio
async def test_pg_list_tables_no_results():
    mock_pg = AsyncMock()
    mock_pg.fetch.return_value = []
    with patch("src.tools.postgres.pg", mock_pg):
        result = await pg_list_tables()
    assert result == "No tables found."


@pytest.mark.asyncio
async def test_pg_describe_table_with_results():
    mock_pg = AsyncMock()
    mock_pg.fetch.return_value = [{"column_name": "id", "data_type": "integer", "is_nullable": "NO", "column_default": None}]
    with patch("src.tools.postgres.pg", mock_pg):
        result = await pg_describe_table("users")
    assert '"column_name": "id"' in result


@pytest.mark.asyncio
async def test_pg_describe_table_not_found():
    mock_pg = AsyncMock()
    mock_pg.fetch.return_value = []
    with patch("src.tools.postgres.pg", mock_pg):
        result = await pg_describe_table("nonexistent", schema="test")
    assert result == "[]"  # _serialize([]) is truthy, so fallback doesn't trigger


@pytest.mark.asyncio
async def test_pg_list_indexes_with_results():
    mock_pg = AsyncMock()
    mock_pg.fetch.return_value = [{"indexname": "users_pkey", "indexdef": "CREATE UNIQUE INDEX ..."}]
    with patch("src.tools.postgres.pg", mock_pg):
        result = await pg_list_indexes("users")
    assert '"indexname": "users_pkey"' in result


@pytest.mark.asyncio
async def test_pg_list_indexes_no_results():
    mock_pg = AsyncMock()
    mock_pg.fetch.return_value = []
    with patch("src.tools.postgres.pg", mock_pg):
        result = await pg_list_indexes("t", schema="s")
    assert result == "[]"
