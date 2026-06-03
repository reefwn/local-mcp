#!/usr/bin/env python3
"""
Example: post a Jira comment with proper ADF formatting.

Prefer jira_add_comment with default markdown formatting.
Use this script only for custom ADF shapes not covered by the markdown converter.

Usage (from local-mcp repo root):
  .venv/bin/python docs/examples/post_adf_comment.py VKR-4136
"""
from __future__ import annotations

import asyncio
import sys

# Run from repo root: PYTHONPATH=. python docs/examples/post_adf_comment.py ISSUE-KEY
from dotenv import load_dotenv

load_dotenv()

from src.config import Config
from src.clients.atlassian import JiraCloudClient


def t(text: str, *, strong: bool = False, code: bool = False) -> dict:
    node: dict = {"type": "text", "text": text}
    marks = []
    if strong:
        marks.append({"type": "strong"})
    if code:
        marks.append({"type": "code"})
    if marks:
        node["marks"] = marks
    return node


def build_example_body() -> dict:
    """Minimal ADF doc — extend or replace content for your issue."""
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [t("Example ADF comment")],
            },
            {
                "type": "paragraph",
                "content": [
                    t("Posted via "),
                    t("docs/examples/post_adf_comment.py", code=True),
                    t(" until "),
                    t("jira_add_comment", code=True),
                    t(" supports markdown."),
                ],
            },
            {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [t("Use bulletList for repo lists")],
                            }
                        ],
                    }
                ],
            },
        ],
    }


async def main(issue_key: str) -> None:
    config = Config()
    client = JiraCloudClient(config)
    try:
        await client.jira_post(
            f"/issue/{issue_key}/comment",
            json={"body": build_example_body()},
        )
        print(f"ADF comment added to {issue_key}.")
    finally:
        await client.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: post_adf_comment.py ISSUE-KEY", file=sys.stderr)
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
