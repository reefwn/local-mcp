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
