import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.tools.figma import (
    _parse_file_key, figma_get_file, figma_get_file_nodes,
    figma_get_images, figma_get_comments, figma_post_comment,
)


def test_parse_file_key_from_url():
    assert _parse_file_key("https://www.figma.com/file/abc123/My-File") == "abc123"


def test_parse_file_key_from_design_url():
    assert _parse_file_key("https://www.figma.com/design/xyz789/File") == "xyz789"


def test_parse_file_key_direct_key():
    assert _parse_file_key("abc123") == "abc123"


def _mock_figma_response(json_data):
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


@pytest.mark.asyncio
async def test_figma_get_file_success():
    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_figma_response({
        "name": "Test", "lastModified": "2023-01-01", "version": "1",
        "document": {}, "components": {}, "styles": {},
    })
    with patch("src.tools.figma._client", mock_client):
        result = await figma_get_file("abc123")
    assert result["name"] == "Test"
    mock_client.get.assert_called_once_with("/files/abc123", params={})


@pytest.mark.asyncio
async def test_figma_get_file_with_depth():
    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_figma_response({"name": "Test"})
    with patch("src.tools.figma._client", mock_client):
        await figma_get_file("abc123", depth=2)
    mock_client.get.assert_called_once_with("/files/abc123", params={"depth": 2})


@pytest.mark.asyncio
async def test_figma_get_file_from_url():
    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_figma_response({"name": "Test"})
    with patch("src.tools.figma._client", mock_client):
        await figma_get_file("https://www.figma.com/file/abc123/Test")
    mock_client.get.assert_called_once_with("/files/abc123", params={})


@pytest.mark.asyncio
async def test_figma_get_file_nodes():
    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_figma_response({"nodes": {"n1": {"type": "FRAME"}}})
    with patch("src.tools.figma._client", mock_client):
        result = await figma_get_file_nodes("abc123", "n1")
    assert result == {"n1": {"type": "FRAME"}}


@pytest.mark.asyncio
async def test_figma_get_images():
    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_figma_response({"images": {"n1": "https://img.png"}})
    with patch("src.tools.figma._client", mock_client):
        result = await figma_get_images("abc123", "n1")
    assert result == {"n1": "https://img.png"}


@pytest.mark.asyncio
async def test_figma_get_comments():
    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_figma_response({
        "comments": [
            {"id": "c1", "message": "Nice", "user": {"handle": "john"}, "created_at": "2023-01-01", "order_id": 1, "parent_id": None},
        ]
    })
    with patch("src.tools.figma._client", mock_client):
        result = await figma_get_comments("abc123")
    assert result[0]["user"] == "john"


@pytest.mark.asyncio
async def test_figma_post_comment_basic():
    mock_client = AsyncMock()
    mock_client.post.return_value = _mock_figma_response({"id": "new"})
    with patch("src.tools.figma._client", mock_client):
        result = await figma_post_comment("abc123", "Hello")
    assert result == {"id": "new"}
    mock_client.post.assert_called_once_with("/files/abc123/comments", json={"message": "Hello"})


@pytest.mark.asyncio
async def test_figma_post_comment_with_node():
    mock_client = AsyncMock()
    mock_client.post.return_value = _mock_figma_response({"id": "new"})
    with patch("src.tools.figma._client", mock_client):
        await figma_post_comment("abc123", "Hello", node_id="n1")
    body = mock_client.post.call_args[1]["json"]
    assert "client_meta" in body


@pytest.mark.asyncio
async def test_figma_post_comment_reply():
    mock_client = AsyncMock()
    mock_client.post.return_value = _mock_figma_response({"id": "reply"})
    with patch("src.tools.figma._client", mock_client):
        await figma_post_comment("abc123", "Reply", comment_id="parent1")
    body = mock_client.post.call_args[1]["json"]
    assert body["comment_id"] == "parent1"
