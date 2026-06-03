"""Convert markdown-ish text to Atlassian Document Format (ADF) for Jira Cloud."""

from __future__ import annotations

import re
from typing import Any

_HEADING_RE = re.compile(r"^(#{2,3})\s+(.+)$")
_BULLET_RE = re.compile(r"^[-*]\s+(.+)$")
_ORDERED_RE = re.compile(r"^\d+\.\s+(.+)$")
_INLINE_RE = re.compile(r"(\*\*(.+?)\*\*|`([^`]+)`)")

ADFDoc = dict[str, Any]


def plain_text_adf(text: str) -> ADFDoc:
    """Single ADF paragraph (legacy plain comment body)."""
    return {
        "type": "doc",
        "version": 1,
        "content": [_paragraph(text)],
    }


def markdown_to_adf(text: str) -> ADFDoc:
    """Convert markdown to a Jira ADF document."""
    lines = text.splitlines()
    content: list[dict[str, Any]] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if line.strip().startswith("```"):
            language = line.strip()[3:].strip() or None
            code_lines: list[str] = []
            i += 1
            while i < len(lines):
                if lines[i].strip() == "```":
                    i += 1
                    break
                code_lines.append(lines[i])
                i += 1
            content.append(_code_block("\n".join(code_lines), language))
            continue

        if not line.strip():
            i += 1
            continue

        heading = _HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            content.append(_heading(heading.group(2), level))
            i += 1
            continue

        bullet_match = _BULLET_RE.match(line)
        if bullet_match:
            items: list[str] = []
            while i < len(lines):
                m = _BULLET_RE.match(lines[i])
                if not m:
                    break
                items.append(m.group(1))
                i += 1
            content.append(_bullet_list(items))
            continue

        ordered_match = _ORDERED_RE.match(line)
        if ordered_match:
            items = []
            while i < len(lines):
                m = _ORDERED_RE.match(lines[i])
                if not m:
                    break
                items.append(m.group(1))
                i += 1
            content.append(_ordered_list(items))
            continue

        block_lines: list[str] = []
        while i < len(lines) and lines[i].strip():
            if _is_block_start(lines[i]):
                break
            block_lines.append(lines[i])
            i += 1
        text_block = "\n".join(block_lines)
        content.append(_paragraph(text_block))

    if not content:
        content.append(_paragraph(""))

    return {"type": "doc", "version": 1, "content": content}


def _is_block_start(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("```"):
        return True
    if _HEADING_RE.match(line):
        return True
    if _BULLET_RE.match(line):
        return True
    if _ORDERED_RE.match(line):
        return True
    return False


def _text_node(text: str, *, strong: bool = False, code: bool = False) -> dict[str, Any]:
    node: dict[str, Any] = {"type": "text", "text": text}
    marks: list[dict[str, str]] = []
    if strong:
        marks.append({"type": "strong"})
    if code:
        marks.append({"type": "code"})
    if marks:
        node["marks"] = marks
    return node


def _parse_inline(text: str) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = []
    pos = 0
    for match in _INLINE_RE.finditer(text):
        if match.start() > pos:
            content.append(_text_node(text[pos : match.start()]))
        if match.group(2) is not None:
            content.append(_text_node(match.group(2), strong=True))
        elif match.group(3) is not None:
            content.append(_text_node(match.group(3), code=True))
        pos = match.end()
    if pos < len(text):
        content.append(_text_node(text[pos:]))
    if not content:
        content.append(_text_node(""))
    return content


def _paragraph(text: str) -> dict[str, Any]:
    return {"type": "paragraph", "content": _parse_inline(text)}


def _heading(text: str, level: int) -> dict[str, Any]:
    return {
        "type": "heading",
        "attrs": {"level": min(level, 6)},
        "content": _parse_inline(text),
    }


def _list_item(text: str) -> dict[str, Any]:
    return {
        "type": "listItem",
        "content": [_paragraph(text)],
    }


def _bullet_list(items: list[str]) -> dict[str, Any]:
    return {
        "type": "bulletList",
        "content": [_list_item(item) for item in items],
    }


def _ordered_list(items: list[str]) -> dict[str, Any]:
    return {
        "type": "orderedList",
        "content": [_list_item(item) for item in items],
    }


def _code_block(text: str, language: str | None) -> dict[str, Any]:
    node: dict[str, Any] = {
        "type": "codeBlock",
        "content": [_text_node(text)],
    }
    if language:
        node["attrs"] = {"language": language}
    return node
