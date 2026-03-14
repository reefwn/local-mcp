import json
import pytest
from unittest.mock import AsyncMock, patch

from src.tools.apm import (
    apm_search_traces,
    apm_get_trace,
    apm_search_errors,
    apm_get_error,
    apm_list_services,
    apm_get_service_metrics,
    apm_find_slow_transactions,
)


@pytest.mark.asyncio
async def test_apm_search_traces():
    mock_es = AsyncMock()
    mock_es.search.return_value = {
        "hits": {"hits": [{"_source": {"transaction.name": "GET /api", "transaction.duration.us": 500000}}]}
    }
    with patch("src.tools.apm.es", mock_es):
        result = await apm_search_traces(service_name="api", size=10)
    
    result_data = json.loads(result)
    assert len(result_data["hits"]["hits"]) == 1


@pytest.mark.asyncio
async def test_apm_get_trace():
    mock_es = AsyncMock()
    mock_es.search.return_value = {
        "hits": {"hits": [{"_source": {"trace.id": "abc", "span.id": "1"}}]}
    }
    with patch("src.tools.apm.es", mock_es):
        result = await apm_get_trace(trace_id="abc")
    
    result_data = json.loads(result)
    assert result_data["hits"]["hits"][0]["_source"]["trace.id"] == "abc"


@pytest.mark.asyncio
async def test_apm_search_errors():
    mock_es = AsyncMock()
    mock_es.search.return_value = {
        "hits": {"hits": [{"_source": {"error.exception.type": "NullPointerException"}}]}
    }
    with patch("src.tools.apm.es", mock_es):
        result = await apm_search_errors(service_name="api", exception_type="NullPointerException")
    
    result_data = json.loads(result)
    assert result_data["hits"]["hits"][0]["_source"]["error.exception.type"] == "NullPointerException"


@pytest.mark.asyncio
async def test_apm_get_error():
    mock_es = AsyncMock()
    mock_es.search.return_value = {
        "hits": {"hits": [{"_source": {"error.id": "err123", "error.log.message": "NPE"}}]}
    }
    with patch("src.tools.apm.es", mock_es):
        result = await apm_get_error(error_id="err123")
    
    result_data = json.loads(result)
    assert result_data["hits"]["hits"][0]["_source"]["error.id"] == "err123"


@pytest.mark.asyncio
async def test_apm_list_services():
    mock_es = AsyncMock()
    mock_es.search.return_value = {
        "aggregations": {"services": {"buckets": [{"key": "api", "doc_count": 100}]}}
    }
    with patch("src.tools.apm.es", mock_es):
        result = await apm_list_services(hours_ago=1)
    
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
    with patch("src.tools.apm.es", mock_es):
        result = await apm_get_service_metrics(service_name="api")
    
    result_data = json.loads(result)
    assert result_data["aggregations"]["transactions"]["count"]["value"] == 1000
    assert result_data["aggregations"]["errors"]["count"]["value"] == 5


@pytest.mark.asyncio
async def test_apm_find_slow_transactions():
    mock_es = AsyncMock()
    mock_es.search.return_value = {
        "hits": {"hits": [{"_source": {"transaction.name": "slow query", "transaction.duration.us": 5000000}}]}
    }
    with patch("src.tools.apm.es", mock_es):
        result = await apm_find_slow_transactions(min_duration_ms=1000)
    
    result_data = json.loads(result)
    assert result_data["hits"]["hits"][0]["_source"]["transaction.duration.us"] == 5000000
