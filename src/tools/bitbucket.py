from src.tools import client, config, mcp


@mcp.tool()
async def bitbucket_list_repos(limit: int = 10) -> str:
    """List repositories in the configured Bitbucket workspace."""
    ws = config.bitbucket_workspace
    data = await client.bitbucket_get(f"/repositories/{ws}", params={"pagelen": limit})
    repos = data.get("values", [])
    return "\n".join(
        f"[{r['slug']}] {r.get('description', 'No description')} (Updated: {r['updated_on'][:10]})"
        for r in repos
    ) or "No repositories found."


@mcp.tool()
async def bitbucket_list_prs(
    repo_slug: str,
    state: str = "OPEN",
    target_branch: str | None = None,
    source_branch: str | None = None,
    author: str | None = None,
) -> str:
    """List pull requests for a Bitbucket repository. State: OPEN, MERGED, DECLINED. Optionally filter by target_branch, source_branch, or author (Atlassian display name or account nickname)."""
    ws = config.bitbucket_workspace
    params: dict = {"state": state}
    filters = []
    if target_branch:
        filters.append(f'destination.branch.name = "{target_branch}"')
    if source_branch:
        filters.append(f'source.branch.name = "{source_branch}"')
    if author:
        filters.append(f'author.display_name ~ "{author}"')
    if filters:
        params["q"] = " AND ".join(filters)
    data = await client.bitbucket_get(
        f"/repositories/{ws}/{repo_slug}/pullrequests",
        params=params,
    )
    prs = data.get("values", [])
    return "\n".join(
        f"[PR #{p['id']}] {p['title']} by {p['author']['display_name']} ({p['state']})"
        for p in prs
    ) or "No pull requests found."


@mcp.tool()
async def bitbucket_get_pr(repo_slug: str, pr_id: int) -> dict:
    """Get details of a specific Bitbucket pull request."""
    ws = config.bitbucket_workspace
    data = await client.bitbucket_get(f"/repositories/{ws}/{repo_slug}/pullrequests/{pr_id}")
    return {
        "id": data["id"],
        "title": data["title"],
        "state": data["state"],
        "author": data["author"]["display_name"],
        "source": data["source"]["branch"]["name"],
        "destination": data["destination"]["branch"]["name"],
        "description": data.get("description", ""),
    }


@mcp.tool()
async def bitbucket_get_pr_diff(repo_slug: str, pr_id: int) -> str:
    """Get the full diff of a pull request."""
    ws = config.bitbucket_workspace
    return await client.bitbucket_get_text(f"/repositories/{ws}/{repo_slug}/pullrequests/{pr_id}/diff")


@mcp.tool()
async def bitbucket_list_pr_comments(repo_slug: str, pr_id: int) -> str:
    """List comments on a pull request."""
    ws = config.bitbucket_workspace
    data = await client.bitbucket_get(f"/repositories/{ws}/{repo_slug}/pullrequests/{pr_id}/comments")
    comments = data.get("values", [])
    return "\n".join(
        f"[{c['user']['display_name']}] {c['content']['raw']}"
        for c in comments
        if c.get("content", {}).get("raw")
    ) or "No comments."


@mcp.tool()
async def bitbucket_update_pr_description(repo_slug: str, pr_id: int, description: str) -> str:
    """Update the description of a Bitbucket pull request."""
    ws = config.bitbucket_workspace
    await client.bitbucket_put(
        f"/repositories/{ws}/{repo_slug}/pullrequests/{pr_id}",
        json={"description": description},
    )
    return f"PR #{pr_id} description updated."


@mcp.tool()
async def bitbucket_create_pr_comment(repo_slug: str, pr_id: int, content: str) -> dict:
    """Post a comment on a pull request."""
    ws = config.bitbucket_workspace
    return await client.bitbucket_post(
        f"/repositories/{ws}/{repo_slug}/pullrequests/{pr_id}/comments",
        json={"content": {"raw": content}},
    )


@mcp.tool()
async def bitbucket_get_repo(repo_slug: str) -> dict:
    """Get repository details including name, description, language, size, and settings."""
    ws = config.bitbucket_workspace
    data = await client.bitbucket_get(f"/repositories/{ws}/{repo_slug}")
    return {
        "slug": data["slug"],
        "name": data["name"],
        "description": data.get("description", ""),
        "language": data.get("language", ""),
        "size": data.get("size", 0),
        "is_private": data.get("is_private", False),
        "created_on": data.get("created_on", ""),
        "updated_on": data.get("updated_on", ""),
        "mainbranch": data.get("mainbranch", {}).get("name", ""),
    }


@mcp.tool()
async def bitbucket_list_branches(repo_slug: str, limit: int = 20) -> str:
    """List branches in a repository."""
    ws = config.bitbucket_workspace
    data = await client.bitbucket_get(
        f"/repositories/{ws}/{repo_slug}/refs/branches",
        params={"pagelen": limit},
    )
    branches = data.get("values", [])
    return "\n".join(
        f"[{b['name']}] Target: {b['target']['hash'][:8]} ({b['target']['date'][:10]})"
        for b in branches
    ) or "No branches found."


@mcp.tool()
async def bitbucket_get_branch(repo_slug: str, branch_name: str) -> dict:
    """Get details of a specific branch."""
    ws = config.bitbucket_workspace
    data = await client.bitbucket_get(f"/repositories/{ws}/{repo_slug}/refs/branches/{branch_name}")
    return {
        "name": data["name"],
        "hash": data["target"]["hash"],
        "author": data["target"]["author"]["raw"],
        "date": data["target"]["date"],
        "message": data["target"]["message"],
    }


@mcp.tool()
async def bitbucket_list_commits(repo_slug: str, branch: str | None = None, limit: int = 10) -> str:
    """List commits in a repository. Optionally filter by branch."""
    ws = config.bitbucket_workspace
    params = {"pagelen": limit}
    path = f"/repositories/{ws}/{repo_slug}/commits"
    if branch:
        path = f"{path}/{branch}"
    data = await client.bitbucket_get(path, params=params)
    commits = data.get("values", [])
    return "\n".join(
        f"[{c['hash'][:8]}] {c['message'].splitlines()[0]} by {c['author']['raw']} ({c['date'][:10]})"
        for c in commits
    ) or "No commits found."


@mcp.tool()
async def bitbucket_get_commit(repo_slug: str, commit_hash: str) -> dict:
    """Get details of a specific commit."""
    ws = config.bitbucket_workspace
    data = await client.bitbucket_get(f"/repositories/{ws}/{repo_slug}/commit/{commit_hash}")
    return {
        "hash": data["hash"],
        "author": data["author"]["raw"],
        "date": data["date"],
        "message": data["message"],
        "parents": [p["hash"] for p in data.get("parents", [])],
    }


@mcp.tool()
async def bitbucket_list_branch_restrictions(repo_slug: str) -> list[dict]:
    """List branch restrictions for a repository."""
    ws = config.bitbucket_workspace
    data = await client.bitbucket_get(f"/repositories/{ws}/{repo_slug}/branch-restrictions")
    restrictions = data.get("values", [])
    return [
        {
            "id": r["id"],
            "kind": r["kind"],
            "pattern": r["pattern"],
            "users": [u["display_name"] for u in r.get("users", [])],
            "groups": [g["name"] for g in r.get("groups", [])],
        }
        for r in restrictions
    ]


@mcp.tool()
async def bitbucket_create_branch_restriction(
    repo_slug: str,
    kind: str,
    pattern: str,
) -> dict:
    """Create a branch restriction. Kind: push, delete, force, restrict_merges, require_approvals_to_merge, require_passing_builds_to_merge, require_tasks_to_be_completed, reset_pullrequest_approvals_on_change, smart_reset_pullrequest_approvals, require_default_reviewer_approvals_to_merge."""
    ws = config.bitbucket_workspace
    return await client.bitbucket_post(
        f"/repositories/{ws}/{repo_slug}/branch-restrictions",
        json={"kind": kind, "pattern": pattern},
    )
