import re

import httpx

from src.tools import config, mcp

_client = httpx.AsyncClient(
    base_url="https://api.figma.com/v1",
    headers={"X-Figma-Token": config.figma_api_token},
    timeout=30.0,
)


def _parse_file_key(file_key_or_url: str) -> str:
    """Extract file key from a Figma URL or return as-is if already a key."""
    m = re.search(r"figma\.com/(?:file|design|proto|board)/([a-zA-Z0-9]+)", file_key_or_url)
    return m.group(1) if m else file_key_or_url


@mcp.tool()
async def figma_get_file(file_key: str, depth: int | None = None) -> dict:
    """Get a Figma file's structure and metadata. Accepts a file key or full Figma URL. Use depth to limit tree traversal (e.g. depth=1 for pages only)."""
    key = _parse_file_key(file_key)
    params = {}
    if depth is not None:
        params["depth"] = depth
    r = await _client.get(f"/files/{key}", params=params)
    r.raise_for_status()
    data = r.json()
    return {
        "name": data.get("name"),
        "lastModified": data.get("lastModified"),
        "version": data.get("version"),
        "document": data.get("document"),
        "components": data.get("components"),
        "styles": data.get("styles"),
    }


@mcp.tool()
async def figma_get_file_nodes(file_key: str, ids: str, depth: int | None = None) -> dict:
    """Get specific nodes from a Figma file by their IDs. ids is a comma-separated list of node IDs (e.g. '1:2,1:3')."""
    key = _parse_file_key(file_key)
    params: dict = {"ids": ids}
    if depth is not None:
        params["depth"] = depth
    r = await _client.get(f"/files/{key}/nodes", params=params)
    r.raise_for_status()
    return r.json().get("nodes", {})


@mcp.tool()
async def figma_get_images(file_key: str, ids: str, scale: float = 1, format: str = "png") -> dict:
    """Export Figma nodes as images. Returns a map of node IDs to image URLs. ids is comma-separated (e.g. '1:2,1:3'). format: png, jpg, svg, pdf."""
    key = _parse_file_key(file_key)
    r = await _client.get(f"/images/{key}", params={"ids": ids, "scale": scale, "format": format})
    r.raise_for_status()
    return r.json().get("images", {})


@mcp.tool()
async def figma_get_comments(file_key: str) -> list[dict]:
    """Get all comments on a Figma file."""
    key = _parse_file_key(file_key)
    r = await _client.get(f"/files/{key}/comments")
    r.raise_for_status()
    comments = r.json().get("comments", [])
    return [
        {
            "id": c["id"],
            "message": c.get("message", ""),
            "user": c.get("user", {}).get("handle", "Unknown"),
            "created_at": c.get("created_at"),
            "order_id": c.get("order_id"),
            "parent_id": c.get("parent_id"),
        }
        for c in comments
    ]


@mcp.tool()
async def figma_post_comment(file_key: str, message: str, node_id: str | None = None, comment_id: str | None = None) -> dict:
    """Post a comment on a Figma file. Optionally pin to a node_id or reply to an existing comment_id."""
    key = _parse_file_key(file_key)
    body: dict = {"message": message}
    if comment_id:
        body["comment_id"] = comment_id
    if node_id:
        body["client_meta"] = {"node_id": node_id, "node_offset": {"x": 0, "y": 0}}
    r = await _client.post(f"/files/{key}/comments", json=body)
    r.raise_for_status()
    return r.json()
