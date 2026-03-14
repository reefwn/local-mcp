import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from src.tools.elasticsearch import (
    elasticsearch_search,
    elasticsearch_aggregate_errors,
    elasticsearch_get_document,
    elasticsearch_list_indices,
    elasticsearch_trace_request,
)


@pytest.mark.asyncio
async def test_elasticsearch_search():
    mock_es = AsyncMock()
    mock_es.search.return_value = {
        "hits": {"total": {"value": 2}, "hits": [{"_id": "1", "_source": {"message": "error"}}]}
    }
    with patch("src.tools.elasticsearch.es", mock_es):
        result = await elasticsearch_search(index="logs-*", query="error", size=10)
    
    result_data = json.loads(result)
    assert result_data["hits"]["total"]["value"] == 2
    mock_es.search.assert_called_once()


@pytest.mark.asyncio
async def test_elasticsearch_aggregate_errors():
    mock_es = AsyncMock()
    mock_es.search.return_value = {
        "aggregations": {
            "error_patterns": {
                "buckets": [{"key": "NullPointerException", "doc_count": 10}]
            }
        }
    }
    with patch("src.tools.elasticsearch.es", mock_es):
        result = await elasticsearch_aggregate_errors(index="logs-*")
    
    result_data = json.loads(result)
    assert result_data["aggregations"]["error_patterns"]["buckets"][0]["doc_count"] == 10


@pytest.mark.asyncio
async def test_elasticsearch_get_document():
    mock_es = AsyncMock()
    mock_es.get_document.return_value = {"_source": {"message": "test log"}}
    with patch("src.tools.elasticsearch.es", mock_es):
        result = await elasticsearch_get_document(index="logs-2024", doc_id="abc123")
    
    result_data = json.loads(result)
    assert result_data["_source"]["message"] == "test log"
    mock_es.get_document.assert_called_once_with("logs-2024", "abc123")


@pytest.mark.asyncio
async def test_elasticsearch_list_indices():
    mock_es = AsyncMock()
    mock_es.list_indices.return_value = [
        {"index": "logs-2024", "docs.count": "1000", "store.size": "1048576"}
    ]
    with patch("src.tools.elasticsearch.es", mock_es):
        result = await elasticsearch_list_indices()
    
    result_data = json.loads(result)
    assert result_data[0]["index"] == "logs-2024"
    assert result_data[0]["docs.count"] == "1000"


@pytest.mark.asyncio
async def test_elasticsearch_trace_request():
    mock_es = AsyncMock()
    mock_es.search.return_value = {
        "hits": {
            "hits": [
                {"_source": {"trace.id": "xyz", "service.name": "api", "span.id": "1"}},
                {"_source": {"trace.id": "xyz", "service.name": "db", "span.id": "2"}},
            ]
        }
    }
    with patch("src.tools.elasticsearch.es", mock_es):
        result = await elasticsearch_trace_request(index="apm-*", trace_id="xyz")
    
    result_data = json.loads(result)
    assert len(result_data["hits"]["hits"]) == 2
    mock_es.search.assert_called_once()
