import json
from unittest.mock import patch

import pytest

from src.tools.obsidian import (
    obsidian_append_content,
    obsidian_complex_search,
    obsidian_delete_file,
    obsidian_get_file_contents,
    obsidian_get_periodic_note,
    obsidian_get_recent_changes,
    obsidian_get_recent_periodic_notes,
    obsidian_list_files_in_dir,
    obsidian_list_files_in_vault,
    obsidian_patch_content,
    obsidian_put_content,
    obsidian_simple_search,
)


@pytest.mark.asyncio
async def test_list_files_in_vault():
    async def mock_list(self): return ["file1.md", "file2.md"]
    mock_client = type("Client", (), {"list_files_in_vault": mock_list})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_list_files_in_vault()
    assert json.loads(result) == ["file1.md", "file2.md"]


@pytest.mark.asyncio
async def test_list_files_in_dir():
    async def mock_list(self, d): return [f"{d}/file.md"]
    mock_client = type("Client", (), {"list_files_in_dir": mock_list})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_list_files_in_dir("notes")
    assert json.loads(result) == ["notes/file.md"]


@pytest.mark.asyncio
async def test_get_file_contents():
    async def mock_get(self, f): return f"Content of {f}"
    mock_client = type("Client", (), {"get_file_contents": mock_get})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_get_file_contents("test.md")
    assert result == "Content of test.md"


@pytest.mark.asyncio
async def test_simple_search():
    async def mock_search(self, q, c): return [{"filename": "test.md", "score": 1.0, "matches": [{"context": "test context", "match": {"start": 0, "end": 4}}]}]
    mock_client = type("Client", (), {"search": mock_search})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_simple_search("test")
    data = json.loads(result)
    assert data[0]["filename"] == "test.md"


@pytest.mark.asyncio
async def test_append_content():
    async def mock_append(self, f, c): pass
    mock_client = type("Client", (), {"append_content": mock_append})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_append_content("test.md", "new content")
    assert "Successfully appended" in result


@pytest.mark.asyncio
async def test_patch_content():
    async def mock_patch(self, *args): pass
    mock_client = type("Client", (), {"patch_content": mock_patch})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_patch_content("test.md", "append", "heading", "## Header", "content")
    assert "Successfully patched" in result


@pytest.mark.asyncio
async def test_put_content():
    async def mock_put(self, f, c): pass
    mock_client = type("Client", (), {"put_content": mock_put})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_put_content("test.md", "content")
    assert "Successfully uploaded" in result


@pytest.mark.asyncio
async def test_delete_file_without_confirm():
    with pytest.raises(ValueError, match="confirm must be set to true"):
        await obsidian_delete_file("test.md", False)


@pytest.mark.asyncio
async def test_delete_file_with_confirm():
    async def mock_delete(self, f): pass
    mock_client = type("Client", (), {"delete_file": mock_delete})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_delete_file("test.md", True)
    assert "Successfully deleted" in result


@pytest.mark.asyncio
async def test_complex_search():
    async def mock_search_json(self, q): return [{"path": "test.md"}]
    mock_client = type("Client", (), {"search_json": mock_search_json})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_complex_search({"glob": ["*.md", {"var": "path"}]})
    assert json.loads(result) == [{"path": "test.md"}]


@pytest.mark.asyncio
async def test_get_periodic_note():
    async def mock_get_note(self, p, t): return f"Note for {p}"
    mock_client = type("Client", (), {"get_periodic_note": mock_get_note})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_get_periodic_note("daily")
    assert result == "Note for daily"


@pytest.mark.asyncio
async def test_get_recent_periodic_notes():
    async def mock_get_recent(self, p, l, i): return [{"date": "2026-03-07"}]
    mock_client = type("Client", (), {"get_recent_periodic_notes": mock_get_recent})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_get_recent_periodic_notes("daily", 5, False)
    assert json.loads(result) == [{"date": "2026-03-07"}]


@pytest.mark.asyncio
async def test_get_recent_changes():
    async def mock_get_changes(self, l, d): return [{"file": "test.md", "mtime": "2026-03-07"}]
    mock_client = type("Client", (), {"get_recent_changes": mock_get_changes})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_get_recent_changes(10, 90)
    assert json.loads(result) == [{"file": "test.md", "mtime": "2026-03-07"}]
