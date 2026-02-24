import pytest
from unittest.mock import AsyncMock, patch
from src.clients.redis import RedisClient


@pytest.mark.asyncio
async def test_redis_client_init():
    client = RedisClient("redis://localhost:6379")
    assert client._url == "redis://localhost:6379"
    assert client._client is None


@pytest.mark.asyncio
async def test_get_client_creates_client():
    with patch('redis.asyncio.from_url') as mock_from_url:
        mock_redis = AsyncMock()
        mock_from_url.return_value = mock_redis
        
        client = RedisClient("redis://localhost:6379")
        redis_client = client._get_client()
        
        assert redis_client == mock_redis
        assert client._client == mock_redis
        mock_from_url.assert_called_once_with("redis://localhost:6379", decode_responses=True)


@pytest.mark.asyncio
async def test_get_client_reuses_existing():
    with patch('redis.asyncio.from_url') as mock_from_url:
        mock_redis = AsyncMock()
        mock_from_url.return_value = mock_redis
        
        client = RedisClient("redis://localhost:6379")
        client1 = client._get_client()
        client2 = client._get_client()
        
        assert client1 == client2
        mock_from_url.assert_called_once()


@pytest.mark.asyncio
async def test_get_success():
    with patch('redis.asyncio.from_url') as mock_from_url:
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "test_value"
        mock_from_url.return_value = mock_redis
        
        client = RedisClient("redis://localhost:6379")
        result = await client.get("test_key")
        
        assert result == "test_value"
        mock_redis.get.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_get_not_found():
    with patch('redis.asyncio.from_url') as mock_from_url:
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_from_url.return_value = mock_redis
        
        client = RedisClient("redis://localhost:6379")
        result = await client.get("nonexistent_key")
        
        assert result is None


@pytest.mark.asyncio
async def test_set_success():
    with patch('redis.asyncio.from_url') as mock_from_url:
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True
        mock_from_url.return_value = mock_redis
        
        client = RedisClient("redis://localhost:6379")
        result = await client.set("test_key", "test_value")
        
        assert result is True
        mock_redis.set.assert_called_once_with("test_key", "test_value", ex=None)


@pytest.mark.asyncio
async def test_set_with_expiry():
    with patch('redis.asyncio.from_url') as mock_from_url:
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True
        mock_from_url.return_value = mock_redis
        
        client = RedisClient("redis://localhost:6379")
        result = await client.set("test_key", "test_value", ex=3600)
        
        assert result is True
        mock_redis.set.assert_called_once_with("test_key", "test_value", ex=3600)


@pytest.mark.asyncio
async def test_delete_success():
    with patch('redis.asyncio.from_url') as mock_from_url:
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 2
        mock_from_url.return_value = mock_redis
        
        client = RedisClient("redis://localhost:6379")
        result = await client.delete("key1", "key2")
        
        assert result == 2
        mock_redis.delete.assert_called_once_with("key1", "key2")


@pytest.mark.asyncio
async def test_keys_success():
    with patch('redis.asyncio.from_url') as mock_from_url:
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = ["key1", "key2"]
        mock_from_url.return_value = mock_redis
        
        client = RedisClient("redis://localhost:6379")
        result = await client.keys("test:*")
        
        assert result == ["key1", "key2"]
        mock_redis.keys.assert_called_once_with("test:*")


@pytest.mark.asyncio
async def test_keys_default_pattern():
    with patch('redis.asyncio.from_url') as mock_from_url:
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = ["key1", "key2"]
        mock_from_url.return_value = mock_redis
        
        client = RedisClient("redis://localhost:6379")
        result = await client.keys()
        
        assert result == ["key1", "key2"]
        mock_redis.keys.assert_called_once_with("*")


@pytest.mark.asyncio
async def test_close_with_client():
    with patch('redis.asyncio.from_url') as mock_from_url:
        mock_redis = AsyncMock()
        mock_from_url.return_value = mock_redis
        
        client = RedisClient("redis://localhost:6379")
        client._get_client()  # Create client
        await client.close()
        
        mock_redis.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_close_without_client():
    client = RedisClient("redis://localhost:6379")
    await client.close()  # Should not raise error