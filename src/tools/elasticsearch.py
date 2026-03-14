"""Elasticsearch tools for log search and debugging."""

import json
from datetime import datetime, timedelta

from src.tools import elasticsearch_client as es, mcp


@mcp.tool()
async def elasticsearch_search(
    index: str,
    query: str,
    size: int = 10,
    time_field: str = "@timestamp",
    hours_ago: int = 24,
) -> str:
    """
    Search Elasticsearch logs with a query string.

    Args:
        index: Index pattern to search (e.g., 'logs-*', 'filebeat-*')
        query: Query string in Lucene syntax (e.g., 'error AND status:500')
        size: Number of results to return (default: 10)
        time_field: Timestamp field name (default: @timestamp)
        hours_ago: Search logs from this many hours ago (default: 24)
    """
    now = datetime.utcnow()
    start_time = now - timedelta(hours=hours_ago)

    body = {
        "query": {
            "bool": {
                "must": [
                    {"query_string": {"query": query}},
                    {"range": {time_field: {"gte": start_time.isoformat(), "lte": now.isoformat()}}},
                ]
            }
        },
        "size": size,
        "sort": [{time_field: {"order": "desc"}}],
    }

    result = await es.search(index, body)
    return json.dumps(result, default=str, indent=2)


@mcp.tool()
async def elasticsearch_aggregate_errors(
    index: str,
    error_field: str = "message",
    time_field: str = "@timestamp",
    hours_ago: int = 24,
    top_n: int = 10,
) -> str:
    """
    Find most common error patterns in logs.

    Args:
        index: Index pattern to search (e.g., 'logs-*')
        error_field: Field containing error messages (default: message)
        time_field: Timestamp field name (default: @timestamp)
        hours_ago: Analyze logs from this many hours ago (default: 24)
        top_n: Number of top errors to return (default: 10)
    """
    now = datetime.utcnow()
    start_time = now - timedelta(hours=hours_ago)

    body = {
        "query": {
            "bool": {
                "must": [
                    {"exists": {"field": error_field}},
                    {"range": {time_field: {"gte": start_time.isoformat(), "lte": now.isoformat()}}},
                ]
            }
        },
        "size": 0,
        "aggs": {"error_patterns": {"terms": {"field": f"{error_field}.keyword", "size": top_n}}},
    }

    result = await es.search(index, body)
    return json.dumps(result, default=str, indent=2)


@mcp.tool()
async def elasticsearch_get_document(index: str, doc_id: str) -> str:
    """
    Get a specific log document by ID.

    Args:
        index: Index name
        doc_id: Document ID
    """
    result = await es.get_document(index, doc_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def elasticsearch_list_indices() -> str:
    """List all Elasticsearch indices with stats."""
    indices = await es.list_indices()
    return json.dumps(indices, indent=2)


@mcp.tool()
async def elasticsearch_trace_request(
    index: str,
    trace_id: str,
    trace_field: str = "trace.id",
    time_field: str = "@timestamp",
) -> str:
    """
    Follow a distributed trace by trace ID.

    Args:
        index: Index pattern to search
        trace_id: Trace ID to follow
        trace_field: Field containing trace ID (default: trace.id)
        time_field: Timestamp field for sorting (default: @timestamp)
    """
    body = {
        "query": {"term": {f"{trace_field}.keyword": trace_id}},
        "size": 100,
        "sort": [{time_field: {"order": "asc"}}],
    }

    result = await es.search(index, body)
    return json.dumps(result, default=str, indent=2)
