from src.tools import client, mcp


@mcp.tool()
async def jira_search(jql: str, max_results: int = 10) -> str:
    """Search Jira issues using JQL query."""
    data = await client.jira_get("/search", params={"jql": jql, "maxResults": max_results})
    issues = data.get("issues", [])
    return "\n".join(
        f"[{i['key']}] {i['fields']['summary']} (Status: {i['fields']['status']['name']})"
        for i in issues
    ) or "No issues found."


@mcp.tool()
async def jira_get_issue(issue_key: str) -> dict:
    """Get details of a specific Jira issue by key (e.g. PROJ-123)."""
    data = await client.jira_get(f"/issue/{issue_key}")
    fields = data["fields"]
    return {
        "key": data["key"],
        "summary": fields["summary"],
        "status": fields["status"]["name"],
        "assignee": (fields.get("assignee") or {}).get("displayName", "Unassigned"),
        "priority": (fields.get("priority") or {}).get("name", "None"),
        "description": fields.get("description"),
    }


@mcp.tool()
async def jira_create_issue(project_key: str, summary: str, issue_type: str = "Task", description: str = "") -> str:
    """Create a new Jira issue."""
    body = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }
    }
    if description:
        body["fields"]["description"] = {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}],
        }
    data = await client.jira_post("/issue", json=body)
    return f"Created {data['key']}: {summary}"
