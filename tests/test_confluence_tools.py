import pytest
from unittest.mock import AsyncMock, patch

from tests.conftest import load_tool_functions

_tools = load_tool_functions("src.tools.confluence")
confluence_search = _tools["confluence_search"]
confluence_get_page = _tools["confluence_get_page"]
confluence_create_page = _tools["confluence_create_page"]


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


@pytest.mark.asyncio
async def test_confluence_create_page_success():
    mock_client = AsyncMock()
    mock_client.confluence_get.return_value = {"results": [{"id": "999"}]}
    mock_client.confluence_post.return_value = {"id": "111", "title": "New Page"}
    with patch("src.tools.confluence.client", mock_client):
        result = await confluence_create_page("ENG", "New Page", "<p>Hello</p>")
    assert result == "Created page [111] New Page"
    mock_client.confluence_get.assert_called_once_with("/spaces", params={"keys": "ENG"})
    mock_client.confluence_post.assert_called_once_with(
        "/pages",
        json={
            "spaceId": "999",
            "status": "current",
            "title": "New Page",
            "body": {"representation": "storage", "value": "<p>Hello</p>"},
        },
    )


@pytest.mark.asyncio
async def test_confluence_create_page_with_parent():
    mock_client = AsyncMock()
    mock_client.confluence_get.return_value = {"results": [{"id": "999"}]}
    mock_client.confluence_post.return_value = {"id": "111", "title": "Child Page"}
    with patch("src.tools.confluence.client", mock_client):
        await confluence_create_page("ENG", "Child Page", "<p>Hi</p>", parent_id="222")
    call_json = mock_client.confluence_post.call_args.kwargs["json"]
    assert call_json["parentId"] == "222"


@pytest.mark.asyncio
async def test_confluence_create_page_space_not_found():
    mock_client = AsyncMock()
    mock_client.confluence_get.return_value = {"results": []}
    with patch("src.tools.confluence.client", mock_client):
        with pytest.raises(ValueError, match="No Confluence space found"):
            await confluence_create_page("NOPE", "Title", "<p>x</p>")
