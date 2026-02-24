import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from src.clients import AtlassianClient


@pytest.mark.asyncio
async def test_atlassian_client_init(mock_config):
    with patch("httpx.AsyncClient") as mock_client:
        client = AtlassianClient(mock_config)
        assert client.config == mock_config
        assert mock_client.call_count == 3


def _make_response(json_data=None, text=""):
    r = MagicMock()
    r.json.return_value = json_data or {}
    r.text = text
    r.raise_for_status = MagicMock()
    return r


@pytest.mark.asyncio
async def test_jira_get_success(mock_atlassian_client):
    mock_atlassian_client._jira.get = AsyncMock(return_value=_make_response({"key": "TEST-1"}))
    result = await mock_atlassian_client.jira_get("/issue/TEST-1")
    assert result == {"key": "TEST-1"}


@pytest.mark.asyncio
async def test_jira_post_success(mock_atlassian_client):
    mock_atlassian_client._jira.post = AsyncMock(return_value=_make_response({"key": "TEST-2"}))
    result = await mock_atlassian_client.jira_post("/issue", json={"fields": {}})
    assert result == {"key": "TEST-2"}


@pytest.mark.asyncio
async def test_confluence_get_success(mock_atlassian_client):
    mock_atlassian_client._confluence.get = AsyncMock(return_value=_make_response({"id": "123"}))
    result = await mock_atlassian_client.confluence_get("/pages/123")
    assert result == {"id": "123"}


@pytest.mark.asyncio
async def test_bitbucket_get_success(mock_atlassian_client):
    mock_atlassian_client._bitbucket.get = AsyncMock(return_value=_make_response({"values": []}))
    result = await mock_atlassian_client.bitbucket_get("/repositories/ws")
    assert result == {"values": []}


@pytest.mark.asyncio
async def test_bitbucket_get_text_success(mock_atlassian_client):
    mock_atlassian_client._bitbucket.get = AsyncMock(return_value=_make_response(text="diff content"))
    result = await mock_atlassian_client.bitbucket_get_text("/diff")
    assert result == "diff content"


@pytest.mark.asyncio
async def test_bitbucket_post_success(mock_atlassian_client):
    mock_atlassian_client._bitbucket.post = AsyncMock(return_value=_make_response({"id": 1}))
    result = await mock_atlassian_client.bitbucket_post("/comments", json={"content": {"raw": "hi"}})
    assert result == {"id": 1}


@pytest.mark.asyncio
async def test_http_error_handling(mock_atlassian_client):
    resp = MagicMock()
    resp.raise_for_status.side_effect = httpx.HTTPStatusError("404", request=MagicMock(), response=MagicMock())
    mock_atlassian_client._jira.get = AsyncMock(return_value=resp)
    with pytest.raises(httpx.HTTPStatusError):
        await mock_atlassian_client.jira_get("/issue/NONEXISTENT")


@pytest.mark.asyncio
async def test_close(mock_atlassian_client):
    await mock_atlassian_client.close()
    mock_atlassian_client._jira.aclose.assert_called_once()
    mock_atlassian_client._confluence.aclose.assert_called_once()
    mock_atlassian_client._bitbucket.aclose.assert_called_once()
