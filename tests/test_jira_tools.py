import pytest
from unittest.mock import AsyncMock, patch

from tests.conftest import load_tool_functions

_tools = load_tool_functions("src.tools.jira")
jira_whoami = _tools["jira_whoami"]
jira_search = _tools["jira_search"]
jira_get_issue = _tools["jira_get_issue"]
jira_create_issue = _tools["jira_create_issue"]
jira_add_comment = _tools["jira_add_comment"]


@pytest.mark.asyncio
async def test_jira_whoami():
    mock_client = AsyncMock()
    mock_client.jira_get.return_value = {
        "accountId": "abc123",
        "displayName": "Jane Doe",
        "emailAddress": "jane@example.com",
        "active": True,
    }
    with patch("src.tools.jira.client", mock_client):
        result = await jira_whoami()
    assert result == {
        "account_id": "abc123",
        "display_name": "Jane Doe",
        "email": "jane@example.com",
        "active": True,
    }
    mock_client.jira_get.assert_called_once_with("/myself")


@pytest.mark.asyncio
async def test_jira_search_with_results():
    mock_client = AsyncMock()
    mock_client.jira_post.return_value = {
        "issues": [
            {"key": "TEST-1", "fields": {"summary": "Issue 1", "status": {"name": "Open"}}},
            {"key": "TEST-2", "fields": {"summary": "Issue 2", "status": {"name": "In Progress"}}},
        ]
    }
    with patch("src.tools.jira.client", mock_client):
        result = await jira_search("project = TEST")
    assert result == "[TEST-1] Issue 1 (Status: Open)\n[TEST-2] Issue 2 (Status: In Progress)"
    mock_client.jira_post.assert_called_once_with("/search/jql", json={"jql": "project = TEST", "maxResults": 10, "fields": ["summary", "status"]})


@pytest.mark.asyncio
async def test_jira_search_no_results():
    mock_client = AsyncMock()
    mock_client.jira_post.return_value = {"issues": []}
    with patch("src.tools.jira.client", mock_client):
        result = await jira_search("project = NONE")
    assert result == "No issues found."


@pytest.mark.asyncio
async def test_jira_search_with_max_results():
    mock_client = AsyncMock()
    mock_client.jira_post.return_value = {"issues": []}
    with patch("src.tools.jira.client", mock_client):
        await jira_search("project = TEST", max_results=5)
    mock_client.jira_post.assert_called_once_with("/search/jql", json={"jql": "project = TEST", "maxResults": 5, "fields": ["summary", "status"]})


@pytest.mark.asyncio
async def test_jira_get_issue_success():
    mock_client = AsyncMock()
    mock_client.jira_get.return_value = {
        "key": "TEST-1",
        "fields": {
            "summary": "Test issue",
            "status": {"name": "Open"},
            "assignee": {"displayName": "John Doe"},
            "priority": {"name": "High"},
            "description": "desc",
        },
    }
    with patch("src.tools.jira.client", mock_client):
        result = await jira_get_issue("TEST-1")
    assert result == {"key": "TEST-1", "summary": "Test issue", "status": "Open", "assignee": "John Doe", "priority": "High", "description": "desc", "custom_fields": {}}


@pytest.mark.asyncio
async def test_jira_get_issue_unassigned():
    mock_client = AsyncMock()
    mock_client.jira_get.return_value = {
        "key": "TEST-1",
        "fields": {"summary": "Test", "status": {"name": "Open"}, "assignee": None, "priority": None, "description": None},
    }
    with patch("src.tools.jira.client", mock_client):
        result = await jira_get_issue("TEST-1")
    assert result["assignee"] == "Unassigned"
    assert result["priority"] == "None"


@pytest.mark.asyncio
async def test_jira_create_issue_basic():
    mock_client = AsyncMock()
    mock_client.jira_post.return_value = {"key": "TEST-3"}
    with patch("src.tools.jira.client", mock_client):
        result = await jira_create_issue("TEST", "New issue")
    assert result == "Created TEST-3: New issue"


@pytest.mark.asyncio
async def test_jira_create_issue_with_description():
    mock_client = AsyncMock()
    mock_client.jira_post.return_value = {"key": "TEST-4"}
    with patch("src.tools.jira.client", mock_client):
        result = await jira_create_issue("TEST", "New issue", "Bug", "A bug")
    assert result == "Created TEST-4: New issue"
    call_body = mock_client.jira_post.call_args[1]["json"]
    assert "description" in call_body["fields"]


@pytest.mark.asyncio
async def test_jira_add_comment_markdown():
    mock_client = AsyncMock()
    mock_client.jira_post.return_value = {}
    with patch("src.tools.jira.client", mock_client):
        result = await jira_add_comment("TEST-1", "## Title\n\n- a\n- b")
    assert result == "Comment added to TEST-1."
    body = mock_client.jira_post.call_args[1]["json"]["body"]
    types = [n["type"] for n in body["content"]]
    assert types == ["heading", "bulletList"]


@pytest.mark.asyncio
async def test_jira_add_comment_plain():
    mock_client = AsyncMock()
    mock_client.jira_post.return_value = {}
    with patch("src.tools.jira.client", mock_client):
        await jira_add_comment("TEST-1", "## not a heading", comment_format="plain")
    body = mock_client.jira_post.call_args[1]["json"]["body"]
    assert body["content"] == [
        {"type": "paragraph", "content": [{"type": "text", "text": "## not a heading"}]}
    ]


@pytest.mark.asyncio
async def test_jira_create_issue_description_uses_markdown_adf():
    mock_client = AsyncMock()
    mock_client.jira_post.return_value = {"key": "TEST-5"}
    with patch("src.tools.jira.client", mock_client):
        await jira_create_issue("TEST", "Issue", description="## Details\n\n- item")
    desc = mock_client.jira_post.call_args[1]["json"]["fields"]["description"]
    types = [n["type"] for n in desc["content"]]
    assert types == ["heading", "bulletList"]
