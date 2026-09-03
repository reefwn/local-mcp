from mcp.server.fastmcp import FastMCP

from src.tools import jira_cloud_client as client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def confluence_search(query: str, limit: int = 10) -> str:
        """Search Confluence pages by title or content."""
        data = await client.confluence_get("/pages", params={"title": query, "limit": limit})
        pages = data.get("results", [])
        return "\n".join(
            f"[{p['id']}] {p['title']} (Status: {p['status']})"
            for p in pages
        ) or "No pages found."

    @mcp.tool()
    async def confluence_get_page(page_id: str) -> dict:
        """Get a Confluence page by ID, including its body content."""
        data = await client.confluence_get(f"/pages/{page_id}", params={"body-format": "storage"})
        return {
            "id": data["id"],
            "title": data["title"],
            "status": data["status"],
            "body": data.get("body", {}).get("storage", {}).get("value", ""),
        }

    @mcp.tool()
    async def confluence_create_page(
        space_key: str, title: str, body: str, parent_id: str = ""
    ) -> str:
        """Create a new Confluence page.

        Args:
            space_key: The space key (e.g. ENG), not the numeric space ID.
            title: Page title.
            body: Page content in Confluence storage format (XHTML, e.g. '<p>Hello</p>').
            parent_id: Optional parent page ID to create this page as a child of.
        """
        spaces = await client.confluence_get("/spaces", params={"keys": space_key})
        results = spaces.get("results", [])
        if not results:
            raise ValueError(f"No Confluence space found with key {space_key!r}.")
        space_id = results[0]["id"]

        page = {
            "spaceId": space_id,
            "status": "current",
            "title": title,
            "body": {"representation": "storage", "value": body},
        }
        if parent_id:
            page["parentId"] = parent_id

        data = await client.confluence_post("/pages", json=page)
        return f"Created page [{data['id']}] {data['title']}"
