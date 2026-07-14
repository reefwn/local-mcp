import json
import pytest
from unittest.mock import AsyncMock, patch

from tests.conftest import load_tool_functions

_tools = load_tool_functions("src.tools.apm")
apm_search_traces = _tools["apm_search_traces"]
apm_get_trace = _tools["apm_get_trace"]
apm_search_errors = _tools["apm_search_errors"]
apm_get_error = _tools["apm_get_error"]
apm_list_services = _tools["apm_list_services"]
apm_get_service_metrics = _tools["apm_get_service_metrics"]
apm_find_slow_transactions = _tools["apm_find_slow_transactions"]


def _patched(mock_es):
    return patch("src.tools.apm.elasticsearch_clients", {"uat": mock_es})


@pytest.mark.asyncio
async def test_apm_search_traces():
    mock_es = AsyncMock()
    mock_es.search.return_value = {
        "hits": {"hits": [{"_source": {"transaction.name": "GET /api", "transaction.duration.us": 500000}}]}
    }
    with _patched(mock_es):
        result = await apm_search_traces(service_name="api", size=10, environment="uat")

    result_data = json.loads(result)
    assert len(result_data["hits"]["hits"]) == 1


@pytest.mark.asyncio
async def test_apm_search_traces_unknown_environment():
    with patch("src.tools.apm.elasticsearch_clients", {}):
        with pytest.raises(ValueError, match="No elasticsearch client configured for environment 'dev'"):
            await apm_search_traces(service_name="api", environment="dev")


@pytest.mark.asyncio
async def test_apm_get_trace():
    mock_es = AsyncMock()
    mock_es.search.return_value = {
        "hits": {"hits": [{"_source": {"trace.id": "abc", "span.id": "1"}}]}
    }
    with _patched(mock_es):
        result = await apm_get_trace(trace_id="abc", environment="uat")

    result_data = json.loads(result)
    assert result_data["hits"]["hits"][0]["_source"]["trace.id"] == "abc"


@pytest.mark.asyncio
async def test_apm_search_errors():
    mock_es = AsyncMock()
    mock_es.search.return_value = {
        "hits": {"hits": [{"_source": {"error.exception.type": "NullPointerException"}}]}
    }
    with _patched(mock_es):
        result = await apm_search_errors(service_name="api", exception_type="NullPointerException", environment="uat")

    result_data = json.loads(result)
    assert result_data["hits"]["hits"][0]["_source"]["error.exception.type"] == "NullPointerException"


@pytest.mark.asyncio
async def test_apm_get_error():
    mock_es = AsyncMock()
    mock_es.search.return_value = {
        "hits": {"hits": [{"_source": {"error.id": "err123", "error.log.message": "NPE"}}]}
    }
    with _patched(mock_es):
        result = await apm_get_error(error_id="err123", environment="uat")

    result_data = json.loads(result)
    assert result_data["hits"]["hits"][0]["_source"]["error.id"] == "err123"


@pytest.mark.asyncio
async def test_apm_list_services():
    mock_es = AsyncMock()
    mock_es.search.return_value = {
        "aggregations": {"services": {"buckets": [{"key": "api", "doc_count": 100}]}}
    }
    with _patched(mock_es):
        result = await apm_list_services(hours_ago=1, environment="uat")

    result_data = json.loads(result)
    assert result_data["aggregations"]["services"]["buckets"][0]["key"] == "api"


@pytest.mark.asyncio
async def test_apm_get_service_metrics():
    mock_es = AsyncMock()
    mock_es.search.return_value = {
        "aggregations": {
            "transactions": {"count": {"value": 1000}, "avg_duration": {"value": 250000}},
            "errors": {"count": {"value": 5}},
        }
    }
    with _patched(mock_es):
        result = await apm_get_service_metrics(service_name="api", environment="uat")

    result_data = json.loads(result)
    assert result_data["aggregations"]["transactions"]["count"]["value"] == 1000
    assert result_data["aggregations"]["errors"]["count"]["value"] == 5


@pytest.mark.asyncio
async def test_apm_find_slow_transactions():
    mock_es = AsyncMock()
    mock_es.search.return_value = {
        "hits": {"hits": [{"_source": {"transaction.name": "slow query", "transaction.duration.us": 5000000}}]}
    }
    with _patched(mock_es):
        result = await apm_find_slow_transactions(min_duration_ms=1000, environment="uat")

    result_data = json.loads(result)
    assert result_data["hits"]["hits"][0]["_source"]["transaction.duration.us"] == 5000000
