from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.clients.observability import LokiClient, TempoClient


@pytest.mark.asyncio
async def test_loki_query_range_uses_query_api():
    client = LokiClient(
        "http://loki:3100",
        token="secret",
        tenant_id="tenant-a",
    )
    response = MagicMock()
    response.json.return_value = {"status": "success", "data": {"result": []}}
    response.raise_for_status = MagicMock()
    http = MagicMock()
    http.get = AsyncMock(return_value=response)

    with patch.object(client, "_get_client", return_value=http):
        result = await client.query_range("{job=\"api\"}", 10, 20, 50, "backward")

    assert result["status"] == "success"
    http.get.assert_awaited_once_with(
        "/loki/api/v1/query_range",
        params={
            "query": '{job="api"}',
            "start": "10",
            "end": "20",
            "limit": 50,
            "direction": "backward",
        },
    )


def test_observability_client_auth_headers():
    client = LokiClient(
        "http://loki:3100",
        token="secret",
        tenant_id="tenant-a",
    )
    http = client._get_client()
    assert http.headers["Authorization"] == "Bearer secret"
    assert http.headers["X-Scope-OrgID"] == "tenant-a"


@pytest.mark.asyncio
async def test_tempo_search_and_trace_paths():
    client = TempoClient("http://tempo:3200")
    response = MagicMock()
    response.json.return_value = {"traces": []}
    response.raise_for_status = MagicMock()
    http = MagicMock()
    http.get = AsyncMock(return_value=response)

    with patch.object(client, "_get_client", return_value=http):
        await client.search("{ status = error }", 100, 200, 20)
        await client.get_trace("abc/123")

    assert http.get.await_args_list[0].args[0] == "/api/search"
    assert http.get.await_args_list[1].args[0] == "/api/v2/traces/abc%2F123"
