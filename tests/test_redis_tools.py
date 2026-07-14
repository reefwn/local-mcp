import pytest
from unittest.mock import AsyncMock, patch

from tests.conftest import load_tool_functions

_tools = load_tool_functions("src.tools.redis")
redis_get = _tools["redis_get"]
redis_keys = _tools["redis_keys"]


def _patched(mock_rd):
    return patch("src.tools.redis.redis_clients", {"uat": mock_rd})


@pytest.mark.asyncio
async def test_redis_get_success():
    mock_rd = AsyncMock()
    mock_rd.get.return_value = "val"
    with _patched(mock_rd):
        result = await redis_get("k", environment="uat")
    assert result == "val"


@pytest.mark.asyncio
async def test_redis_get_not_found():
    mock_rd = AsyncMock()
    mock_rd.get.return_value = None
    with _patched(mock_rd):
        result = await redis_get("missing", environment="uat")
    assert result == "Key 'missing' not found."


@pytest.mark.asyncio
async def test_redis_get_unknown_environment():
    with patch("src.tools.redis.redis_clients", {}):
        with pytest.raises(ValueError, match="No redis client configured for environment 'dev'"):
            await redis_get("k", environment="dev")


@pytest.mark.asyncio
async def test_redis_keys_with_results():
    mock_rd = AsyncMock()
    mock_rd.keys.return_value = ["k1", "k2"]
    with _patched(mock_rd):
        result = await redis_keys(pattern="test:*", environment="uat")
    assert '"k1"' in result
    assert '"k2"' in result


@pytest.mark.asyncio
async def test_redis_keys_no_results():
    mock_rd = AsyncMock()
    mock_rd.keys.return_value = []
    with _patched(mock_rd):
        result = await redis_keys(pattern="none:*", environment="uat")
    assert result == "No keys found."
