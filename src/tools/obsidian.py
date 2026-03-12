import json

from src.tools import config, mcp, obsidian_client as client


@mcp.tool()
async def obsidian_list_files_in_vault() -> str:
    """Lists all files and directories in the root directory of your Obsidian vault."""
    files = await client.list_files_in_vault()
    return json.dumps(files, indent=2)


@mcp.tool()
async def obsidian_list_files_in_dir(dirpath: str) -> str:
    """Lists all files and directories in a specific Obsidian directory."""
    files = await client.list_files_in_dir(dirpath)
    return json.dumps(files, indent=2)


@mcp.tool()
async def obsidian_get_file_contents(filepath: str) -> str:
    """Return the content of a single file in your vault."""
    return await client.get_file_contents(filepath)


@mcp.tool()
async def obsidian_simple_search(query: str, context_length: int = 100) -> str:
    """Simple search for documents matching a specified text query across all files in the vault."""
    results = await client.search(query, context_length)
    formatted = [
        {
            "filename": r.get("filename", ""),
            "score": r.get("score", 0),
            "matches": [
                {"context": m.get("context", ""), "match_position": m.get("match", {})} for m in r.get("matches", [])
            ],
        }
        for r in results
    ]
    return json.dumps(formatted, indent=2)


@mcp.tool()
async def obsidian_append_content(filepath: str, content: str) -> str:
    """Append content to a new or existing file in the vault."""
    await client.append_content(filepath, content)
    return f"Successfully appended content to {filepath}"


@mcp.tool()
async def obsidian_patch_content(filepath: str, operation: str, target_type: str, target: str, content: str) -> str:
    """Insert content into an existing note relative to a heading, block reference, or frontmatter field.
    
    Args:
        filepath: Path to the file (relative to vault root)
        operation: Operation to perform (append, prepend, or replace)
        target_type: Type of target to patch (heading, block, or frontmatter)
        target: Target identifier:
            - For headings: Use heading text WITHOUT # symbols, separated by :: for nested headings
              Examples: "My Heading", "Parent Heading::Child Heading", "H1::H2::H3"
            - For blocks: Use the block reference ID (e.g., "abc123")
            - For frontmatter: Use the field name (e.g., "tags")
        content: Content to insert
    """
    await client.patch_content(filepath, operation, target_type, target, content)
    return f"Successfully patched content in {filepath}"


@mcp.tool()
async def obsidian_put_content(filepath: str, content: str) -> str:
    """Create a new file in your vault or update the content of an existing one."""
    await client.put_content(filepath, content)
    return f"Successfully uploaded content to {filepath}"


@mcp.tool()
async def obsidian_delete_file(filepath: str, confirm: bool = False) -> str:
    """Delete a file or directory from the vault. Requires confirm=True."""
    if not confirm:
        raise ValueError("confirm must be set to true to delete a file")
    await client.delete_file(filepath)
    return f"Successfully deleted {filepath}"


@mcp.tool()
async def obsidian_complex_search(query: dict) -> str:
    """Complex search using JsonLogic query. Supports 'glob' and 'regexp' operators.
    
    Examples:
    - Match all markdown files: {"glob": ["*.md", {"var": "path"}]}
    - Match markdown files with substring: {"and": [{"glob": ["*.md", {"var": "path"}]}, {"regexp": [".*1221.*", {"var": "content"}]}]}
    """
    results = await client.search_json(query)
    return json.dumps(results, indent=2)


@mcp.tool()
async def obsidian_get_periodic_note(period: str, type: str = "content") -> str:
    """Get current periodic note for the specified period.
    
    Args:
        period: The period type (daily, weekly, monthly, quarterly, yearly)
        type: Type of data to get ('content' or 'metadata')
    """
    return await client.get_periodic_note(period, type)


@mcp.tool()
async def obsidian_get_recent_periodic_notes(period: str, limit: int = 5, include_content: bool = False) -> str:
    """Get most recent periodic notes for the specified period type.
    
    Args:
        period: The period type (daily, weekly, monthly, quarterly, yearly)
        limit: Maximum number of notes to return (default: 5)
        include_content: Whether to include note content (default: False)
    """
    results = await client.get_recent_periodic_notes(period, limit, include_content)
    return json.dumps(results, indent=2)


@mcp.tool()
async def obsidian_get_recent_changes(limit: int = 10, days: int = 90) -> str:
    """Get recently modified files in the vault.
    
    Args:
        limit: Maximum number of files to return (default: 10)
        days: Only include files modified within this many days (default: 90)
    """
    results = await client.get_recent_changes(limit, days)
    return json.dumps(results, indent=2)
