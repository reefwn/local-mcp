import pytest
from unittest.mock import AsyncMock, patch
from src.clients.postgres import PostgresClient


@pytest.mark.asyncio
async def test_postgres_client_init():
    client = PostgresClient("postgresql://test:test@localhost/test")
    assert client._url == "postgresql://test:test@localhost/test"
    assert client._pool is None


@pytest.mark.asyncio
async def test_get_pool_creates_pool():
    mock_pool = AsyncMock()
    with patch("asyncpg.create_pool", new_callable=AsyncMock, return_value=mock_pool):
        client = PostgresClient("postgresql://test:test@localhost/test")
        pool = await client._get_pool()
        assert pool is mock_pool


@pytest.mark.asyncio
async def test_get_pool_reuses_existing():
    mock_pool = AsyncMock()
    with patch("asyncpg.create_pool", new_callable=AsyncMock, return_value=mock_pool) as mock_create:
        client = PostgresClient("postgresql://test:test@localhost/test")
        await client._get_pool()
        await client._get_pool()
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_success():
    mock_pool = AsyncMock()
    mock_pool.fetch.return_value = [{"id": 1, "name": "test"}]
    with patch("asyncpg.create_pool", new_callable=AsyncMock, return_value=mock_pool):
        client = PostgresClient("postgresql://test:test@localhost/test")
        result = await client.fetch("SELECT 1")
    assert result == [{"id": 1, "name": "test"}]


@pytest.mark.asyncio
async def test_fetch_empty():
    mock_pool = AsyncMock()
    mock_pool.fetch.return_value = []
    with patch("asyncpg.create_pool", new_callable=AsyncMock, return_value=mock_pool):
        client = PostgresClient("postgresql://test:test@localhost/test")
        result = await client.fetch("SELECT 1")
    assert result == []


@pytest.mark.asyncio
async def test_execute_success():
    mock_pool = AsyncMock()
    mock_pool.execute.return_value = "INSERT 0 1"
    with patch("asyncpg.create_pool", new_callable=AsyncMock, return_value=mock_pool):
        client = PostgresClient("postgresql://test:test@localhost/test")
        result = await client.execute("INSERT INTO t VALUES ($1)", "x")
    assert result == "INSERT 0 1"


@pytest.mark.asyncio
async def test_close_without_pool():
    client = PostgresClient("postgresql://test:test@localhost/test")
    await client.close()  # no error
