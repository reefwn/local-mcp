import pytest
from unittest.mock import AsyncMock, patch
from src.tools.jira import jira_search, jira_get_issue, jira_create_issue, jira_add_comment


@pytest.mark.asyncio
async def test_jira_search_with_results():
    mock_client = AsyncMock()
    mock_client.jira_get.return_value = {
        "issues": [
            {"key": "TEST-1", "fields": {"summary": "Issue 1", "status": {"name": "Open"}}},
            {"key": "TEST-2", "fields": {"summary": "Issue 2", "status": {"name": "In Progress"}}},
        ]
    }
    with patch("src.tools.jira.client", mock_client):
        result = await jira_search("project = TEST")
    assert result == "[TEST-1] Issue 1 (Status: Open)\n[TEST-2] Issue 2 (Status: In Progress)"
    mock_client.jira_get.assert_called_once_with("/search", params={"jql": "project = TEST", "maxResults": 10})


@pytest.mark.asyncio
async def test_jira_search_no_results():
    mock_client = AsyncMock()
    mock_client.jira_get.return_value = {"issues": []}
    with patch("src.tools.jira.client", mock_client):
        result = await jira_search("project = NONE")
    assert result == "No issues found."


@pytest.mark.asyncio
async def test_jira_search_with_max_results():
    mock_client = AsyncMock()
    mock_client.jira_get.return_value = {"issues": []}
    with patch("src.tools.jira.client", mock_client):
        await jira_search("project = TEST", max_results=5)
    mock_client.jira_get.assert_called_once_with("/search", params={"jql": "project = TEST", "maxResults": 5})


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
    assert result == {"key": "TEST-1", "summary": "Test issue", "status": "Open", "assignee": "John Doe", "priority": "High", "description": "desc"}


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
async def test_jira_add_comment():
    mock_client = AsyncMock()
    mock_client.jira_post.return_value = {}
    with patch("src.tools.jira.client", mock_client):
        result = await jira_add_comment("TEST-1", "A comment")
    assert result == "Comment added to TEST-1."
