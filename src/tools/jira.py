import json

from src.tools import atlassian_client as client, config, mcp


@mcp.tool()
async def jira_search(jql: str, max_results: int = 10) -> str:
    """Search Jira issues using JQL query. Returns a list of matching issues with key, summary, and status."""
    data = await client.jira_post("/search/jql", json={"jql": jql, "maxResults": max_results, "fields": ["summary", "status"]})
    issues = data.get("issues", [])
    return "\n".join(
        f"[{i['key']}] {i['fields']['summary']} (Status: {i['fields']['status']['name']})"
        for i in issues
    ) or "No issues found."


@mcp.tool()
async def jira_get_issue(issue_key: str) -> dict:
    """Get details of a specific Jira issue by key (e.g. PROJ-123).

    Returns summary, status, assignee, priority, description, and all non-null custom fields.
    Custom fields are returned under the 'custom_fields' key as a dict of field_id to value.
    Use this to discover custom field IDs before calling jira_update_custom_field.
    """
    data = await client.jira_get(f"/issue/{issue_key}")
    fields = data["fields"]
    result = {
        "key": data["key"],
        "summary": fields["summary"],
        "status": fields["status"]["name"],
        "assignee": (fields.get("assignee") or {}).get("displayName", "Unassigned"),
        "priority": (fields.get("priority") or {}).get("name", "None"),
        "description": fields.get("description"),
        "custom_fields": {k: v for k, v in fields.items() if k.startswith("customfield_") and v is not None},
    }
    return result


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


@mcp.tool()
async def jira_add_comment(issue_key: str, comment: str) -> str:
    """Add a comment to a Jira issue by key (e.g. PROJ-123)."""
    body = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment}]}],
        }
    }
    await client.jira_post(f"/issue/{issue_key}/comment", json=body)
    return f"Comment added to {issue_key}."


@mcp.tool()
async def jira_update_custom_field(issue_key: str, field_id: str, value: str) -> str:
    """Update a custom field on a Jira issue.

    Use jira_get_issue first to discover available custom field IDs and their current values.

    Args:
        issue_key: The issue key (e.g. PROJ-123).
        field_id: The custom field ID (e.g. customfield_10001). Get this from jira_get_issue.
        value: The field value as a JSON string. The format depends on the field type:
            - String field: '"some text"'
            - Number field: '42'
            - Single select: '{"value": "Option A"}'
            - Multi select: '[{"value": "A"}, {"value": "B"}]'
            - User picker: '{"accountId": "abc123"}'
            - Date field: '"2024-01-15"'
            - Clear a field: 'null'
    """
    parsed = json.loads(value)
    await client.jira_put(f"/issue/{issue_key}", json={"fields": {field_id: parsed}})
    return f"Updated {field_id} on {issue_key}."


@mcp.tool()
async def jira_list_comments(issue_key: str) -> list[dict]:
    """List all comments on a Jira issue by key (e.g. PROJ-123)."""
    data = await client.jira_get(f"/issue/{issue_key}/comment")
    return [
        {
            "id": c["id"],
            "author": c.get("author", {}).get("displayName", "Unknown"),
            "body": c.get("body"),
            "created": c.get("created"),
        }
        for c in data.get("comments", [])
    ]


@mcp.tool()
async def jira_get_comment(issue_key: str, comment_id: str) -> dict:
    """Get a specific comment on a Jira issue by issue key and comment ID."""
    c = await client.jira_get(f"/issue/{issue_key}/comment/{comment_id}")
    return {
        "id": c["id"],
        "author": c.get("author", {}).get("displayName", "Unknown"),
        "body": c.get("body"),
        "created": c.get("created"),
        "updated": c.get("updated"),
    }


@mcp.tool()
async def jira_list_transitions(issue_key: str) -> list[dict]:
    """List available status transitions for a Jira issue. Use this to find valid transition IDs before calling jira_update_status."""
    data = await client.jira_get(f"/issue/{issue_key}/transitions")
    return [{"id": t["id"], "name": t["name"], "to": t["to"]["name"]} for t in data.get("transitions", [])]


@mcp.tool()
async def jira_update_status(issue_key: str, transition_id: str) -> str:
    """Update the status of a Jira issue by performing a transition.

    Use jira_list_transitions first to get available transition IDs for the issue.

    Args:
        issue_key: The issue key (e.g. PROJ-123).
        transition_id: The transition ID from jira_list_transitions.
    """
    await client.jira_post(f"/issue/{issue_key}/transitions", json={"transition": {"id": transition_id}})
    return f"Transitioned {issue_key} with transition {transition_id}."