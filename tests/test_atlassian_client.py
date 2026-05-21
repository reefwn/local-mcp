import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from src.clients import BitbucketClient, JiraCloudClient


@pytest.mark.asyncio
async def test_jira_cloud_client_init(mock_config):
    with patch("httpx.AsyncClient") as mock_client:
        client = JiraCloudClient(mock_config)
        assert client.config == mock_config
        assert mock_client.call_count == 1


@pytest.mark.asyncio
async def test_jira_cloud_client_separate_confluence_auth(mock_config):
    mock_config.confluence_email = "conf@example.com"
    mock_config.confluence_api_token = "conf-token"
    jira_http = AsyncMock()
    confluence_http = AsyncMock()
    with patch("httpx.AsyncClient", side_effect=[jira_http, confluence_http]):
        client = JiraCloudClient(mock_config)
        assert client._jira is jira_http
        assert client._confluence is confluence_http


def _make_response(json_data=None, text=""):
    r = MagicMock()
    r.json.return_value = json_data or {}
    r.text = text
    r.raise_for_status = MagicMock()
    return r


@pytest.mark.asyncio
async def test_jira_get_success(mock_jira_cloud_client):
    mock_jira_cloud_client._jira.get = AsyncMock(return_value=_make_response({"key": "TEST-1"}))
    result = await mock_jira_cloud_client.jira_get("/issue/TEST-1")
    assert result == {"key": "TEST-1"}


@pytest.mark.asyncio
async def test_jira_post_success(mock_jira_cloud_client):
    mock_jira_cloud_client._jira.post = AsyncMock(return_value=_make_response({"key": "TEST-2"}))
    result = await mock_jira_cloud_client.jira_post("/issue", json={"fields": {}})
    assert result == {"key": "TEST-2"}


@pytest.mark.asyncio
async def test_confluence_get_success(mock_jira_cloud_client):
    mock_jira_cloud_client._confluence.get = AsyncMock(return_value=_make_response({"id": "123"}))
    result = await mock_jira_cloud_client.confluence_get("/pages/123")
    assert result == {"id": "123"}


@pytest.mark.asyncio
async def test_bitbucket_client_init(mock_config):
    with patch("httpx.AsyncClient") as mock_client:
        client = BitbucketClient(mock_config)
        assert client.config == mock_config
        assert mock_client.call_count == 1


@pytest.mark.asyncio
async def test_bitbucket_get_success(mock_bitbucket_client):
    mock_bitbucket_client._http.get = AsyncMock(return_value=_make_response({"values": []}))
    result = await mock_bitbucket_client.get("/repositories/ws")
    assert result == {"values": []}


@pytest.mark.asyncio
async def test_bitbucket_get_text_success(mock_bitbucket_client):
    mock_bitbucket_client._http.get = AsyncMock(return_value=_make_response(text="diff content"))
    result = await mock_bitbucket_client.get_text("/diff")
    assert result == "diff content"


@pytest.mark.asyncio
async def test_bitbucket_post_success(mock_bitbucket_client):
    mock_bitbucket_client._http.post = AsyncMock(return_value=_make_response({"id": 1}))
    result = await mock_bitbucket_client.post("/comments", json={"content": {"raw": "hi"}})
    assert result == {"id": 1}


@pytest.mark.asyncio
async def test_http_error_handling(mock_jira_cloud_client):
    resp = MagicMock()
    resp.raise_for_status.side_effect = httpx.HTTPStatusError("404", request=MagicMock(), response=MagicMock())
    mock_jira_cloud_client._jira.get = AsyncMock(return_value=resp)
    with pytest.raises(httpx.HTTPStatusError):
        await mock_jira_cloud_client.jira_get("/issue/NONEXISTENT")


@pytest.mark.asyncio
async def test_jira_cloud_client_close(mock_jira_cloud_client):
    await mock_jira_cloud_client.close()
    mock_jira_cloud_client._jira.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_jira_cloud_client_close_separate_confluence(mock_config):
    mock_config.confluence_email = "conf@example.com"
    mock_config.confluence_api_token = "conf-token"
    jira_http = AsyncMock()
    confluence_http = AsyncMock()
    with patch("httpx.AsyncClient", side_effect=[jira_http, confluence_http]):
        client = JiraCloudClient(mock_config)
        await client.close()
        jira_http.aclose.assert_called_once()
        confluence_http.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_bitbucket_client_close(mock_bitbucket_client):
    await mock_bitbucket_client.close()
    mock_bitbucket_client._http.aclose.assert_called_once()
