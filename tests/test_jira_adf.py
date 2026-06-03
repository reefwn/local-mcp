from src.jira.adf import markdown_to_adf, plain_text_adf


def test_plain_text_adf():
    doc = plain_text_adf("hello")
    assert doc == {
        "type": "doc",
        "version": 1,
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": "hello"}]}],
    }


def test_heading_and_paragraph():
    doc = markdown_to_adf("## Title\n\nBody text")
    types = [n["type"] for n in doc["content"]]
    assert types == ["heading", "paragraph"]
    assert doc["content"][0]["attrs"]["level"] == 2
    assert doc["content"][0]["content"][0]["text"] == "Title"
    assert doc["content"][1]["content"][0]["text"] == "Body text"


def test_bullet_list():
    doc = markdown_to_adf("- a\n- b")
    assert len(doc["content"]) == 1
    bl = doc["content"][0]
    assert bl["type"] == "bulletList"
    assert len(bl["content"]) == 2
    assert bl["content"][0]["content"][0]["content"][0]["text"] == "a"


def test_ordered_list():
    doc = markdown_to_adf("1. first\n2. second")
    assert doc["content"][0]["type"] == "orderedList"
    items = doc["content"][0]["content"]
    assert items[0]["content"][0]["content"][0]["text"] == "first"
    assert items[1]["content"][0]["content"][0]["text"] == "second"


def test_code_block():
    doc = markdown_to_adf("```python\nprint('hi')\n```")
    block = doc["content"][0]
    assert block["type"] == "codeBlock"
    assert block["attrs"]["language"] == "python"
    assert block["content"][0]["text"] == "print('hi')"


def test_inline_bold_and_code():
    doc = markdown_to_adf("Use **bold** and `code` here")
    nodes = doc["content"][0]["content"]
    assert nodes[1]["marks"] == [{"type": "strong"}]
    assert nodes[3]["marks"] == [{"type": "code"}]


def test_mixed_summary_snippet():
    md = """## Deploy summary

- Run migrations
- Restart API

```bash
docker compose up -d
```

**Done** when green."""
    doc = markdown_to_adf(md)
    types = [n["type"] for n in doc["content"]]
    assert types[0] == "heading"
    assert "bulletList" in types
    assert "codeBlock" in types
    last_para = doc["content"][-1]
    assert any(n.get("marks") == [{"type": "strong"}] for n in last_para["content"])


def test_heading_plus_bullet_list():
    doc = markdown_to_adf("## Title\n\n- a\n- b")
    types = [n["type"] for n in doc["content"]]
    assert types == ["heading", "bulletList"]
