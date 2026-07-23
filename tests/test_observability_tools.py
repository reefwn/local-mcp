import json
from unittest.mock import AsyncMock, patch

import pytest


def _load_registered(register_name: str) -> dict:
    from mcp.server.fastmcp import FastMCP
    from src.tools import observability

    mcp = FastMCP("test")
    getattr(observability, register_name)(mcp)
    return {name: tool.fn for name, tool in mcp._tool_manager._tools.items()}


_loki_tools = _load_registered("register_loki")
_tempo_tools = _load_registered("register_tempo")


@pytest.mark.asyncio
async def test_loki_search_logs_aggregates_and_sorts_environments():
    dev = AsyncMock()
    prod = AsyncMock()
    dev.query_range.return_value = {
        "data": {
            "result": [
                {"stream": {"service": "api"}, "values": [["100", "dev older"]]}
            ]
        }
    }
    prod.query_range.return_value = {
        "data": {
            "result": [
                {"stream": {"service": "api"}, "values": [["200", "prod newer"]]}
            ]
        }
    }
    with patch("src.tools.observability.loki_clients", {"dev": dev, "prod": prod}):
        result = await _loki_tools["loki_search_logs"](
            query='{service="api"}',
            environment="all",
            limit=10,
        )

    data = json.loads(result)
    assert data["environments"] == ["dev", "prod"]
    assert [entry["line"] for entry in data["entries"]] == ["prod newer", "dev older"]
    assert [entry["environment"] for entry in data["entries"]] == ["prod", "dev"]


@pytest.mark.asyncio
async def test_loki_search_logs_keeps_partial_results():
    dev = AsyncMock()
    prod = AsyncMock()
    dev.query_range.side_effect = TimeoutError("offline")
    prod.query_range.return_value = {
        "data": {"result": [{"stream": {}, "values": [["200", "available"]]}]}
    }
    with patch("src.tools.observability.loki_clients", {"dev": dev, "prod": prod}):
        result = await _loki_tools["loki_search_logs"](query="{job=\"api\"}")

    data = json.loads(result)
    assert data["entries"][0]["line"] == "available"
    assert "dev" in data["errors"]


@pytest.mark.asyncio
async def test_loki_list_labels_returns_union():
    dev = AsyncMock()
    prod = AsyncMock()
    dev.labels.return_value = {"data": ["job", "service"]}
    prod.labels.return_value = {"data": ["cluster", "service"]}
    with patch("src.tools.observability.loki_clients", {"dev": dev, "prod": prod}):
        result = await _loki_tools["loki_list_labels"]()

    assert json.loads(result)["labels"] == ["cluster", "job", "service"]


@pytest.mark.asyncio
async def test_tempo_search_traces_aggregates_and_limits():
    qa = AsyncMock()
    prod = AsyncMock()
    qa.search.return_value = {
        "traces": [{"traceID": "old", "startTimeUnixNano": "100"}]
    }
    prod.search.return_value = {
        "traces": [{"traceID": "new", "startTimeUnixNano": "200"}]
    }
    with patch("src.tools.observability.tempo_clients", {"qa": qa, "prod": prod}):
        result = await _tempo_tools["tempo_search_traces"](limit=1)

    data = json.loads(result)
    assert data["count"] == 1
    assert data["traces"][0]["traceID"] == "new"
    assert data["traces"][0]["environment"] == "prod"


@pytest.mark.asyncio
async def test_tempo_get_trace_checks_all_environments():
    qa = AsyncMock()
    prod = AsyncMock()
    qa.get_trace.return_value = {"trace": "qa"}
    prod.get_trace.return_value = {"trace": "prod"}
    with patch("src.tools.observability.tempo_clients", {"qa": qa, "prod": prod}):
        result = await _tempo_tools["tempo_get_trace"](trace_id="abc")

    data = json.loads(result)
    assert [match["environment"] for match in data["matches"]] == ["prod", "qa"]


@pytest.mark.asyncio
async def test_tempo_list_services_returns_union():
    dev = AsyncMock()
    uat = AsyncMock()
    dev.tag_values.return_value = {
        "tagValues": [{"type": "string", "value": "checkout"}]
    }
    uat.tag_values.return_value = {
        "tagValues": [
            {"type": "string", "value": "checkout"},
            {"type": "string", "value": "payment"},
        ]
    }
    with patch("src.tools.observability.tempo_clients", {"dev": dev, "uat": uat}):
        result = await _tempo_tools["tempo_list_services"]()

    assert json.loads(result)["services"] == ["checkout", "payment"]
