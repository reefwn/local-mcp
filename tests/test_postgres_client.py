import asyncpg
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.clients.postgres import PostgresClient


@pytest.mark.asyncio
async def test_postgres_client_init():
    client = PostgresClient("postgresql://test:test@localhost/test")
    assert client._host == "localhost"
    assert client._port == 5432
    assert client._user == "test"
    assert client._password == "test"
    assert client._default_database == "test"
    assert client._pools == {}


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


def _mock_fetch_pool(mock_conn):
    """Create a mock pool where acquire() and transaction() are sync calls returning async context managers."""
    mock_tx = MagicMock()
    mock_tx.__aenter__ = AsyncMock(return_value=None)
    mock_tx.__aexit__ = AsyncMock(return_value=False)
    mock_conn.transaction = MagicMock(return_value=mock_tx)

    mock_acq = MagicMock()
    mock_acq.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_acq.__aexit__ = AsyncMock(return_value=False)

    mock_pool = AsyncMock()
    mock_pool.acquire = MagicMock(return_value=mock_acq)
    return mock_pool


@pytest.mark.asyncio
async def test_fetch_success():
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = [{"id": 1, "name": "test"}]
    mock_pool = _mock_fetch_pool(mock_conn)
    with patch("asyncpg.create_pool", new_callable=AsyncMock, return_value=mock_pool):
        client = PostgresClient("postgresql://test:test@localhost/test")
        result = await client.fetch(query="SELECT 1")
    mock_conn.transaction.assert_called_once_with(readonly=True)
    assert result == [{"id": 1, "name": "test"}]


@pytest.mark.asyncio
async def test_fetch_empty():
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = []
    mock_pool = _mock_fetch_pool(mock_conn)
    with patch("asyncpg.create_pool", new_callable=AsyncMock, return_value=mock_pool):
        client = PostgresClient("postgresql://test:test@localhost/test")
        result = await client.fetch(query="SELECT 1")
    mock_conn.transaction.assert_called_once_with(readonly=True)
    assert result == []


@pytest.mark.asyncio
async def test_fetch_rejects_write_query():
    mock_conn = AsyncMock()
    mock_conn.fetch.side_effect = asyncpg.ReadOnlySQLTransactionError("cannot execute INSERT in a read-only transaction")
    mock_pool = _mock_fetch_pool(mock_conn)
    with patch("asyncpg.create_pool", new_callable=AsyncMock, return_value=mock_pool):
        client = PostgresClient("postgresql://test:test@localhost/test")
        with pytest.raises(asyncpg.ReadOnlySQLTransactionError):
            await client.fetch(query="INSERT INTO t VALUES (1)")


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
