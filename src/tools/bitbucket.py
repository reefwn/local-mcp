from mcp.server.fastmcp import FastMCP

from src.clients.atlassian import format_bitbucket_pipeline_ref, format_bitbucket_uuid
from src.tools import bitbucket_client as client, config

_PR_STATES = frozenset({"OPEN", "MERGED", "DECLINED"})


def _require_non_empty(value: str, field: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field} is required and must be a non-empty string.")
    return stripped


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def bitbucket_list_repos(limit: int = 10) -> str:
        """List repositories in the configured Bitbucket workspace."""
        ws = config.bitbucket_workspace
        data = await client.get(f"/repositories/{ws}", params={"pagelen": limit})
        repos = data.get("values", [])
        return "\n".join(
            f"[{r['slug']}] {r.get('description', 'No description')} (Updated: {r['updated_on'][:10]})"
            for r in repos
        ) or "No repositories found."

    @mcp.tool()
    async def bitbucket_list_prs(
        repo_slug: str,
        state: str = "OPEN",
        target_branch: str = "",
        source_branch: str = "",
        author: str = "",
    ) -> str:
        """List pull requests for a Bitbucket repository. State: OPEN, MERGED, DECLINED. Optionally filter by target_branch, source_branch, or author (Atlassian display name or account nickname). Leave optional filters empty to omit them."""
        repo_slug = _require_non_empty(repo_slug, "repo_slug")
        state = state.strip().upper()
        if state not in _PR_STATES:
            raise ValueError(f"state must be one of {sorted(_PR_STATES)}, got {state!r}.")
        ws = config.bitbucket_workspace
        params: dict = {"state": state}
        filters = []
        if target_branch.strip():
            filters.append(f'destination.branch.name = "{target_branch.strip()}"')
        if source_branch.strip():
            filters.append(f'source.branch.name = "{source_branch.strip()}"')
        if author.strip():
            filters.append(f'author.display_name ~ "{author.strip()}"')
        if filters:
            params["q"] = " AND ".join(filters)
        data = await client.get(
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
        data = await client.get(f"/repositories/{ws}/{repo_slug}/pullrequests/{pr_id}")
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
        return await client.get_text(f"/repositories/{ws}/{repo_slug}/pullrequests/{pr_id}/diff")

    @mcp.tool()
    async def bitbucket_list_pr_comments(repo_slug: str, pr_id: int) -> str:
        """List comments on a pull request."""
        ws = config.bitbucket_workspace
        data = await client.get(f"/repositories/{ws}/{repo_slug}/pullrequests/{pr_id}/comments")
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
        await client.put(
            f"/repositories/{ws}/{repo_slug}/pullrequests/{pr_id}",
            json={"description": description},
        )
        return f"PR #{pr_id} description updated."

    @mcp.tool()
    async def bitbucket_update_pr_reviewers(repo_slug: str, pr_id: int, reviewers: list[str]) -> str:
        """Update the reviewers of a Bitbucket pull request. Reviewers is a list of user UUIDs. This replaces the current reviewer list entirely."""
        ws = config.bitbucket_workspace
        await client.put(
            f"/repositories/{ws}/{repo_slug}/pullrequests/{pr_id}",
            json={"reviewers": [{"uuid": uuid} for uuid in reviewers]},
        )
        return f"PR #{pr_id} reviewers updated."

    @mcp.tool()
    async def bitbucket_create_pr_comment(repo_slug: str, pr_id: int, content: str) -> dict:
        """Post a comment on a pull request."""
        ws = config.bitbucket_workspace
        return await client.post(
            f"/repositories/{ws}/{repo_slug}/pullrequests/{pr_id}/comments",
            json={"content": {"raw": content}},
        )

    @mcp.tool()
    async def bitbucket_create_pr(
        repo_slug: str,
        title: str,
        source_branch: str,
        destination_branch: str = "",
        description: str = "",
        close_source_branch: bool = False,
        reviewers: list[str] | None = None,
    ) -> dict:
        """Create a new pull request. If destination_branch is empty, the repo's main branch is used. Reviewers is a list of user UUIDs to add as reviewers."""
        repo_slug = _require_non_empty(repo_slug, "repo_slug")
        title = _require_non_empty(title, "title")
        source_branch = _require_non_empty(source_branch, "source_branch")
        ws = config.bitbucket_workspace
        body: dict = {
            "title": title,
            "source": {"branch": {"name": source_branch}},
            "description": description,
            "close_source_branch": close_source_branch,
        }
        if destination_branch.strip():
            body["destination"] = {"branch": {"name": destination_branch.strip()}}
        if reviewers:
            body["reviewers"] = [{"uuid": uuid} for uuid in reviewers]
        data = await client.post(
            f"/repositories/{ws}/{repo_slug}/pullrequests",
            json=body,
        )
        return {
            "id": data["id"],
            "title": data["title"],
            "state": data["state"],
            "source": data["source"]["branch"]["name"],
            "destination": data["destination"]["branch"]["name"],
            "url": data["links"]["html"]["href"],
        }

    @mcp.tool()
    async def bitbucket_get_repo(repo_slug: str) -> dict:
        """Get repository details including name, description, language, size, and settings."""
        ws = config.bitbucket_workspace
        data = await client.get(f"/repositories/{ws}/{repo_slug}")
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
        data = await client.get(
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
        data = await client.get(f"/repositories/{ws}/{repo_slug}/refs/branches/{branch_name}")
        return {
            "name": data["name"],
            "hash": data["target"]["hash"],
            "author": data["target"]["author"]["raw"],
            "date": data["target"]["date"],
            "message": data["target"]["message"],
        }

    @mcp.tool()
    async def bitbucket_list_commits(repo_slug: str, branch: str = "", limit: int = 10) -> str:
        """List commits in a repository. Optionally filter by branch (leave empty for default)."""
        ws = config.bitbucket_workspace
        params = {"pagelen": limit}
        path = f"/repositories/{ws}/{repo_slug}/commits"
        if branch.strip():
            path = f"{path}/{branch.strip()}"
        data = await client.get(path, params=params)
        commits = data.get("values", [])
        return "\n".join(
            f"[{c['hash'][:8]}] {c['message'].splitlines()[0]} by {c['author']['raw']} ({c['date'][:10]})"
            for c in commits
        ) or "No commits found."

    @mcp.tool()
    async def bitbucket_get_commit(repo_slug: str, commit_hash: str) -> dict:
        """Get details of a specific commit."""
        ws = config.bitbucket_workspace
        data = await client.get(f"/repositories/{ws}/{repo_slug}/commit/{commit_hash}")
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
        data = await client.get(f"/repositories/{ws}/{repo_slug}/branch-restrictions")
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
    async def bitbucket_list_pipelines(repo_slug: str, limit: int = 10) -> str:
        """List recent CI/CD pipelines for a repository. Shows build number, status, branch, and trigger info."""
        ws = config.bitbucket_workspace
        data = await client.get(
            f"/repositories/{ws}/{repo_slug}/pipelines",
            params={"pagelen": limit, "sort": "-created_on"},
        )
        pipelines = data.get("values", [])
        lines = []
        for p in pipelines:
            num = p.get("build_number", "?")
            state = p.get("state", {})
            status = state.get("name", "UNKNOWN")
            result = state.get("result", {}).get("name", "") if status == "COMPLETED" else ""
            target = p.get("target", {})
            branch = target.get("ref_name", target.get("selector", {}).get("pattern", "N/A"))
            created = p.get("created_on", "")[:19]
            display = f"{status}/{result}" if result else status
            uuid = p.get("uuid", "")
            lines.append(f"[#{num}] {uuid} | {display} | {branch} | {created}")
        return "\n".join(lines) or "No pipelines found."

    @mcp.tool()
    async def bitbucket_get_pipeline(repo_slug: str, pipeline_uuid: str) -> dict:
        """Get details of a specific pipeline by build number or UUID (braces optional)."""
        ws = config.bitbucket_workspace
        pipeline_ref = format_bitbucket_pipeline_ref(pipeline_uuid)
        data = await client.get(f"/repositories/{ws}/{repo_slug}/pipelines/{pipeline_ref}")
        state = data.get("state", {})
        return {
            "uuid": data.get("uuid"),
            "build_number": data.get("build_number"),
            "status": state.get("name"),
            "result": state.get("result", {}).get("name") if state.get("name") == "COMPLETED" else None,
            "branch": data.get("target", {}).get("ref_name"),
            "trigger": data.get("trigger", {}).get("name"),
            "created_on": data.get("created_on"),
            "completed_on": data.get("completed_on"),
            "build_seconds_used": data.get("build_seconds_used"),
        }

    @mcp.tool()
    async def bitbucket_list_pipeline_steps(repo_slug: str, pipeline_uuid: str) -> str:
        """List steps for a given pipeline. Shows step name, status, and duration. pipeline_uuid may be a build number or UUID."""
        ws = config.bitbucket_workspace
        pipeline_ref = format_bitbucket_pipeline_ref(pipeline_uuid)
        data = await client.get(
            f"/repositories/{ws}/{repo_slug}/pipelines/{pipeline_ref}/steps",
        )
        steps = data.get("values", [])
        lines = []
        for s in steps:
            uuid = s.get("uuid", "")
            name = s.get("name", "unnamed")
            state = s.get("state", {})
            status = state.get("name", "UNKNOWN")
            result = state.get("result", {}).get("name", "") if status == "COMPLETED" else ""
            started = s.get("started_on", "")[:19]
            display = f"{status}/{result}" if result else status
            lines.append(f"[{uuid}] {name} | {display} | started: {started}")
        return "\n".join(lines) or "No steps found."

    @mcp.tool()
    async def bitbucket_get_pipeline_step_log(repo_slug: str, pipeline_uuid: str, step_uuid: str) -> str:
        """Get the log output for a specific step of a pipeline. pipeline_uuid may be a build number (e.g. 263) or UUID (with or without braces). step_uuid is the step UUID (braces optional)."""
        repo_slug = _require_non_empty(repo_slug, "repo_slug")
        ws = config.bitbucket_workspace
        pipeline_ref = format_bitbucket_pipeline_ref(pipeline_uuid)
        step_ref = format_bitbucket_uuid(step_uuid, label="step_uuid")
        return await client.get_binary_text(
            f"/repositories/{ws}/{repo_slug}/pipelines/{pipeline_ref}/steps/{step_ref}/log",
        )

    @mcp.tool()
    async def bitbucket_create_branch_restriction(repo_slug: str, kind: str, pattern: str) -> dict:
        """Create a branch restriction. Kind: push, delete, force, restrict_merges, require_approvals_to_merge, require_passing_builds_to_merge, require_tasks_to_be_completed, reset_pullrequest_approvals_on_change, smart_reset_pullrequest_approvals, require_default_reviewer_approvals_to_merge."""
        ws = config.bitbucket_workspace
        return await client.post(
            f"/repositories/{ws}/{repo_slug}/branch-restrictions",
            json={"kind": kind, "pattern": pattern},
        )

    @mcp.tool()
    async def bitbucket_list_workspace_members() -> list[dict]:
        """List members of the configured Bitbucket workspace. Returns display names and UUIDs, useful for finding reviewer UUIDs."""
        ws = config.bitbucket_workspace
        data = await client.get(f"/workspaces/{ws}/members")
        return [
            {"display_name": m["user"]["display_name"], "uuid": m["user"]["uuid"]}
            for m in data.get("values", [])
            if m.get("user")
        ]

    @mcp.tool()
    async def bitbucket_list_default_reviewers(repo_slug: str) -> list[dict]:
        """List effective default reviewers for a repository. Includes both repo-level and project-inherited reviewers with their UUIDs."""
        ws = config.bitbucket_workspace
        data = await client.get(f"/repositories/{ws}/{repo_slug}/effective-default-reviewers")
        return [
            {
                "display_name": r["user"]["display_name"],
                "uuid": r["user"]["uuid"],
                "reviewer_type": r.get("reviewer_type", "repository"),
            }
            for r in data.get("values", [])
        ]
