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
    mock_client = type("Client", (), {"obsidian": type("Obsidian", (), {"list_files_in_vault": lambda: ["file1.md", "file2.md"]})()})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_list_files_in_vault()
    assert json.loads(result) == ["file1.md", "file2.md"]


@pytest.mark.asyncio
async def test_list_files_in_dir():
    mock_client = type("Client", (), {"obsidian": type("Obsidian", (), {"list_files_in_dir": lambda d: [f"{d}/file.md"]})()})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_list_files_in_dir("notes")
    assert json.loads(result) == ["notes/file.md"]


@pytest.mark.asyncio
async def test_get_file_contents():
    mock_client = type("Client", (), {"obsidian": type("Obsidian", (), {"get_file_contents": lambda f: f"Content of {f}"})()})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_get_file_contents("test.md")
    assert result == "Content of test.md"


@pytest.mark.asyncio
async def test_simple_search():
    mock_client = type(
        "Client",
        (),
        {
            "obsidian": type(
                "Obsidian",
                (),
                {
                    "search": lambda q, c: [
                        {"filename": "test.md", "score": 1.0, "matches": [{"context": "test context", "match": {"start": 0, "end": 4}}]}
                    ]
                },
            )()
        },
    )()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_simple_search("test")
    data = json.loads(result)
    assert data[0]["filename"] == "test.md"


@pytest.mark.asyncio
async def test_append_content():
    mock_client = type("Client", (), {"obsidian": type("Obsidian", (), {"append_content": lambda f, c: None})()})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_append_content("test.md", "new content")
    assert "Successfully appended" in result


@pytest.mark.asyncio
async def test_patch_content():
    mock_client = type("Client", (), {"obsidian": type("Obsidian", (), {"patch_content": lambda *args: None})()})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_patch_content("test.md", "append", "heading", "## Header", "content")
    assert "Successfully patched" in result


@pytest.mark.asyncio
async def test_put_content():
    mock_client = type("Client", (), {"obsidian": type("Obsidian", (), {"put_content": lambda f, c: None})()})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_put_content("test.md", "content")
    assert "Successfully uploaded" in result


@pytest.mark.asyncio
async def test_delete_file_without_confirm():
    with pytest.raises(ValueError, match="confirm must be set to true"):
        await obsidian_delete_file("test.md", False)


@pytest.mark.asyncio
async def test_delete_file_with_confirm():
    mock_client = type("Client", (), {"obsidian": type("Obsidian", (), {"delete_file": lambda f: None})()})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_delete_file("test.md", True)
    assert "Successfully deleted" in result


@pytest.mark.asyncio
async def test_complex_search():
    mock_client = type("Client", (), {"obsidian": type("Obsidian", (), {"search_json": lambda q: [{"path": "test.md"}]})()})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_complex_search({"glob": ["*.md", {"var": "path"}]})
    assert json.loads(result) == [{"path": "test.md"}]


@pytest.mark.asyncio
async def test_get_periodic_note():
    mock_client = type("Client", (), {"obsidian": type("Obsidian", (), {"get_periodic_note": lambda p, t: f"Note for {p}"})()})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_get_periodic_note("daily")
    assert result == "Note for daily"


@pytest.mark.asyncio
async def test_get_recent_periodic_notes():
    mock_client = type("Client", (), {"obsidian": type("Obsidian", (), {"get_recent_periodic_notes": lambda p, l, i: [{"date": "2026-03-07"}]})()})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_get_recent_periodic_notes("daily", 5, False)
    assert json.loads(result) == [{"date": "2026-03-07"}]


@pytest.mark.asyncio
async def test_get_recent_changes():
    mock_client = type("Client", (), {"obsidian": type("Obsidian", (), {"get_recent_changes": lambda l, d: [{"file": "test.md", "mtime": "2026-03-07"}]})()})()
    with patch("src.tools.obsidian.client", mock_client):
        result = await obsidian_get_recent_changes(10, 90)
    assert json.loads(result) == [{"file": "test.md", "mtime": "2026-03-07"}]
