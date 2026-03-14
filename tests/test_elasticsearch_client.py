import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.clients.elasticsearch import ElasticsearchClient


@pytest.mark.asyncio
async def test_search():
    client = ElasticsearchClient(url="http://localhost:9200")
    mock_response = MagicMock()
    mock_response.json.return_value = {"hits": {"total": {"value": 1}}}
    mock_response.raise_for_status = MagicMock()
    
    with patch.object(client, "_get_client") as mock_get_client:
        mock_http_client = MagicMock()
        mock_http_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_http_client
        
        result = await client.search("logs-*", {"query": {"match_all": {}}})
    
    assert result["hits"]["total"]["value"] == 1
    mock_http_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_get_document():
    client = ElasticsearchClient(url="http://localhost:9200")
    mock_response = MagicMock()
    mock_response.json.return_value = {"_source": {"message": "test"}}
    mock_response.raise_for_status = MagicMock()
    
    with patch.object(client, "_get_client") as mock_get_client:
        mock_http_client = MagicMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_http_client
        
        result = await client.get_document("logs-2024", "abc123")
    
    assert result["_source"]["message"] == "test"


@pytest.mark.asyncio
async def test_list_indices():
    client = ElasticsearchClient(url="http://localhost:9200")
    mock_response = MagicMock()
    mock_response.json.return_value = [{"index": "logs-2024", "docs.count": "100"}]
    mock_response.raise_for_status = MagicMock()
    
    with patch.object(client, "_get_client") as mock_get_client:
        mock_http_client = MagicMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_http_client
        
        result = await client.list_indices()
    
    assert len(result) == 1
    assert result[0]["index"] == "logs-2024"


@pytest.mark.asyncio
async def test_client_with_api_key():
    client = ElasticsearchClient(url="http://localhost:9200", api_key="test-key")
    http_client = client._get_client()
    
    assert "Authorization" in http_client.headers
    assert http_client.headers["Authorization"] == "ApiKey test-key"


@pytest.mark.asyncio
async def test_client_with_basic_auth():
    client = ElasticsearchClient(url="http://localhost:9200", username="user", password="pass")
    http_client = client._get_client()
    
    assert http_client._auth is not None
