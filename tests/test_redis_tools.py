import pytest
from unittest.mock import AsyncMock, patch
from src.tools.redis import redis_get, redis_set, redis_delete, redis_keys


@pytest.mark.asyncio
async def test_redis_get_success():
    mock_rd = AsyncMock()
    mock_rd.get.return_value = "val"
    with patch("src.tools.redis.rd", mock_rd):
        result = await redis_get("k")
    assert result == "val"


@pytest.mark.asyncio
async def test_redis_get_not_found():
    mock_rd = AsyncMock()
    mock_rd.get.return_value = None
    with patch("src.tools.redis.rd", mock_rd):
        result = await redis_get("missing")
    assert result == "Key 'missing' not found."


@pytest.mark.asyncio
async def test_redis_set_success():
    mock_rd = AsyncMock()
    with patch("src.tools.redis.rd", mock_rd):
        result = await redis_set("k", "v")
    assert "OK" in result
    mock_rd.set.assert_called_once_with("k", "v", ex=None)


@pytest.mark.asyncio
async def test_redis_set_with_ttl():
    mock_rd = AsyncMock()
    with patch("src.tools.redis.rd", mock_rd):
        result = await redis_set("k", "v", ttl=60)
    mock_rd.set.assert_called_once_with("k", "v", ex=60)


@pytest.mark.asyncio
async def test_redis_delete_success():
    mock_rd = AsyncMock()
    mock_rd.delete.return_value = 2
    with patch("src.tools.redis.rd", mock_rd):
        result = await redis_delete("k")
    assert result == "Deleted 2 key(s)."


@pytest.mark.asyncio
async def test_redis_keys_with_results():
    mock_rd = AsyncMock()
    mock_rd.keys.return_value = ["k1", "k2"]
    with patch("src.tools.redis.rd", mock_rd):
        result = await redis_keys("test:*")
    assert '"k1"' in result
    assert '"k2"' in result


@pytest.mark.asyncio
async def test_redis_keys_no_results():
    mock_rd = AsyncMock()
    mock_rd.keys.return_value = []
    with patch("src.tools.redis.rd", mock_rd):
        result = await redis_keys("none:*")
    assert result == "No keys found."
