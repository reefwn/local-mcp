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
async def bitbucket_list_prs(repo_slug: str, state: str = "OPEN") -> str:
    """List pull requests for a Bitbucket repository. State: OPEN, MERGED, DECLINED."""
    ws = config.bitbucket_workspace
    data = await client.bitbucket_get(
        f"/repositories/{ws}/{repo_slug}/pullrequests",
        params={"state": state},
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
