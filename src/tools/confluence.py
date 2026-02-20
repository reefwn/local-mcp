from src.tools import client, mcp


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
