import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.tools.bitbucket import (
    bitbucket_list_repos, bitbucket_list_prs, bitbucket_get_pr,
    bitbucket_get_pr_diff, bitbucket_list_pr_comments, bitbucket_create_pr_comment,
    bitbucket_create_pr, bitbucket_list_workspace_members, bitbucket_list_default_reviewers,
)


def _patches():
    mock_client = AsyncMock()
    mock_config = MagicMock()
    mock_config.bitbucket_workspace = "test-ws"
    return mock_client, mock_config


@pytest.mark.asyncio
async def test_bitbucket_list_repos_with_results():
    mc, cfg = _patches()
    mc.bitbucket_get.return_value = {
        "values": [
            {"slug": "repo1", "description": "Desc", "updated_on": "2023-01-01T00:00:00Z"},
        ]
    }
    with patch("src.tools.bitbucket.client", mc), patch("src.tools.bitbucket.config", cfg):
        result = await bitbucket_list_repos()
    assert "[repo1]" in result


@pytest.mark.asyncio
async def test_bitbucket_list_repos_no_results():
    mc, cfg = _patches()
    mc.bitbucket_get.return_value = {"values": []}
    with patch("src.tools.bitbucket.client", mc), patch("src.tools.bitbucket.config", cfg):
        result = await bitbucket_list_repos()
    assert result == "No repositories found."


@pytest.mark.asyncio
async def test_bitbucket_list_prs_basic():
    mc, cfg = _patches()
    mc.bitbucket_get.return_value = {
        "values": [{"id": 1, "title": "PR 1", "author": {"display_name": "John"}, "state": "OPEN"}]
    }
    with patch("src.tools.bitbucket.client", mc), patch("src.tools.bitbucket.config", cfg):
        result = await bitbucket_list_prs("repo")
    assert "[PR #1]" in result


@pytest.mark.asyncio
async def test_bitbucket_list_prs_with_filters():
    mc, cfg = _patches()
    mc.bitbucket_get.return_value = {"values": []}
    with patch("src.tools.bitbucket.client", mc), patch("src.tools.bitbucket.config", cfg):
        await bitbucket_list_prs("repo", state="MERGED", target_branch="main", source_branch="feat", author="John")
    params = mc.bitbucket_get.call_args[1]["params"]
    assert "destination.branch.name" in params["q"]
    assert "source.branch.name" in params["q"]
    assert "author.display_name" in params["q"]


@pytest.mark.asyncio
async def test_bitbucket_get_pr_success():
    mc, cfg = _patches()
    mc.bitbucket_get.return_value = {
        "id": 1, "title": "PR", "state": "OPEN",
        "author": {"display_name": "John"},
        "source": {"branch": {"name": "feat"}},
        "destination": {"branch": {"name": "main"}},
        "description": "desc",
    }
    with patch("src.tools.bitbucket.client", mc), patch("src.tools.bitbucket.config", cfg):
        result = await bitbucket_get_pr("repo", 1)
    assert result["author"] == "John"
    assert result["source"] == "feat"


@pytest.mark.asyncio
async def test_bitbucket_get_pr_diff():
    mc, cfg = _patches()
    mc.bitbucket_get_text.return_value = "diff --git a/f b/f"
    with patch("src.tools.bitbucket.client", mc), patch("src.tools.bitbucket.config", cfg):
        result = await bitbucket_get_pr_diff("repo", 1)
    assert result.startswith("diff")


@pytest.mark.asyncio
async def test_bitbucket_list_pr_comments():
    mc, cfg = _patches()
    mc.bitbucket_get.return_value = {
        "values": [
            {"user": {"display_name": "John"}, "content": {"raw": "LGTM"}},
            {"user": {"display_name": "Bob"}, "content": {}},
        ]
    }
    with patch("src.tools.bitbucket.client", mc), patch("src.tools.bitbucket.config", cfg):
        result = await bitbucket_list_pr_comments("repo", 1)
    assert "[John] LGTM" in result
    assert "Bob" not in result


@pytest.mark.asyncio
async def test_bitbucket_create_pr_comment():
    mc, cfg = _patches()
    mc.bitbucket_post.return_value = {"id": "c1"}
    with patch("src.tools.bitbucket.client", mc), patch("src.tools.bitbucket.config", cfg):
        result = await bitbucket_create_pr_comment("repo", 1, "Nice")
    assert result == {"id": "c1"}


_PR_RESPONSE = {
    "id": 42,
    "title": "My PR",
    "state": "OPEN",
    "source": {"branch": {"name": "feat"}},
    "destination": {"branch": {"name": "main"}},
    "links": {"html": {"href": "https://bitbucket.org/test-ws/repo/pull-requests/42"}},
}


@pytest.mark.asyncio
async def test_bitbucket_create_pr_basic():
    mc, cfg = _patches()
    mc.bitbucket_post.return_value = _PR_RESPONSE
    with patch("src.tools.bitbucket.client", mc), patch("src.tools.bitbucket.config", cfg):
        result = await bitbucket_create_pr("repo", "My PR", "feat")
    body = mc.bitbucket_post.call_args[1]["json"]
    assert body["source"] == {"branch": {"name": "feat"}}
    assert "reviewers" not in body
    assert result["id"] == 42


@pytest.mark.asyncio
async def test_bitbucket_create_pr_with_reviewers():
    mc, cfg = _patches()
    mc.bitbucket_post.return_value = _PR_RESPONSE
    uuids = ["{uuid-1}", "{uuid-2}"]
    with patch("src.tools.bitbucket.client", mc), patch("src.tools.bitbucket.config", cfg):
        result = await bitbucket_create_pr("repo", "My PR", "feat", reviewers=uuids)
    body = mc.bitbucket_post.call_args[1]["json"]
    assert body["reviewers"] == [{"uuid": "{uuid-1}"}, {"uuid": "{uuid-2}"}]
    assert result["url"] == "https://bitbucket.org/test-ws/repo/pull-requests/42"


@pytest.mark.asyncio
async def test_bitbucket_list_workspace_members():
    mc, cfg = _patches()
    mc.bitbucket_get.return_value = {
        "values": [
            {"user": {"display_name": "Alice", "uuid": "{uuid-a}"}},
            {"user": {"display_name": "Bob", "uuid": "{uuid-b}"}},
        ]
    }
    with patch("src.tools.bitbucket.client", mc), patch("src.tools.bitbucket.config", cfg):
        result = await bitbucket_list_workspace_members()
    mc.bitbucket_get.assert_called_once_with("/workspaces/test-ws/members")
    assert result == [
        {"display_name": "Alice", "uuid": "{uuid-a}"},
        {"display_name": "Bob", "uuid": "{uuid-b}"},
    ]


@pytest.mark.asyncio
async def test_bitbucket_list_default_reviewers():
    mc, cfg = _patches()
    mc.bitbucket_get.return_value = {
        "values": [
            {"user": {"display_name": "Alice", "uuid": "{uuid-a}"}, "reviewer_type": "project", "type": "default_reviewer"},
            {"user": {"display_name": "Bob", "uuid": "{uuid-b}"}, "reviewer_type": "repository", "type": "default_reviewer"},
        ]
    }
    with patch("src.tools.bitbucket.client", mc), patch("src.tools.bitbucket.config", cfg):
        result = await bitbucket_list_default_reviewers("my-repo")
    mc.bitbucket_get.assert_called_once_with("/repositories/test-ws/my-repo/effective-default-reviewers")
    assert result == [
        {"display_name": "Alice", "uuid": "{uuid-a}", "reviewer_type": "project"},
        {"display_name": "Bob", "uuid": "{uuid-b}", "reviewer_type": "repository"},
    ]
