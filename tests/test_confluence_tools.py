import pytest
from unittest.mock import AsyncMock, patch
from src.tools.confluence import confluence_search, confluence_get_page


@pytest.mark.asyncio
async def test_confluence_search_with_results():
    mock_client = AsyncMock()
    mock_client.confluence_get.return_value = {
        "results": [
            {"id": "123", "title": "Page 1", "status": "current"},
            {"id": "456", "title": "Page 2", "status": "current"},
        ]
    }
    with patch("src.tools.confluence.client", mock_client):
        result = await confluence_search("test")
    assert result == "[123] Page 1 (Status: current)\n[456] Page 2 (Status: current)"


@pytest.mark.asyncio
async def test_confluence_search_no_results():
    mock_client = AsyncMock()
    mock_client.confluence_get.return_value = {"results": []}
    with patch("src.tools.confluence.client", mock_client):
        result = await confluence_search("nonexistent")
    assert result == "No pages found."


@pytest.mark.asyncio
async def test_confluence_get_page_success():
    mock_client = AsyncMock()
    mock_client.confluence_get.return_value = {
        "id": "123",
        "title": "Test Page",
        "status": "current",
        "body": {"storage": {"value": "<p>Content</p>"}},
    }
    with patch("src.tools.confluence.client", mock_client):
        result = await confluence_get_page("123")
    assert result == {"id": "123", "title": "Test Page", "status": "current", "body": "<p>Content</p>"}


@pytest.mark.asyncio
async def test_confluence_get_page_no_body():
    mock_client = AsyncMock()
    mock_client.confluence_get.return_value = {"id": "123", "title": "Test", "status": "current"}
    with patch("src.tools.confluence.client", mock_client):
        result = await confluence_get_page("123")
    assert result["body"] == ""
