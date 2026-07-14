"""Elastic APM tools for application performance monitoring and debugging."""

import json
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP

from src.tools import elasticsearch_clients, resolve_client


def _client(environment: str):
    return resolve_client(elasticsearch_clients, environment, "elasticsearch")


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def apm_search_traces(
        environment: str,
        service_name: str = "",
        transaction_type: str = "",
        min_duration_ms: int = 0,
        hours_ago: int = 24,
        size: int = 10,
    ) -> str:
        """
        Search APM traces by service, transaction type, or duration.

        Args:
            environment: Target environment (dev, qa, uat, prod).
            service_name: Filter by service name (optional)
            transaction_type: Filter by transaction type like 'request' (optional)
            min_duration_ms: Minimum transaction duration in milliseconds (optional)
            hours_ago: Search traces from this many hours ago (default: 24)
            size: Number of results to return (default: 10)
        """
        now = datetime.utcnow()
        start_time = now - timedelta(hours=hours_ago)
        must = [
            {"term": {"processor.event": "transaction"}},
            {"range": {"@timestamp": {"gte": start_time.isoformat(), "lte": now.isoformat()}}},
        ]
        if service_name:
            must.append({"term": {"service.name": service_name}})
        if transaction_type:
            must.append({"term": {"transaction.type": transaction_type}})
        if min_duration_ms > 0:
            must.append({"range": {"transaction.duration.us": {"gte": min_duration_ms * 1000}}})
        body = {
            "query": {"bool": {"must": must}},
            "size": size,
            "sort": [{"transaction.duration.us": {"order": "desc"}}],
        }
        result = await _client(environment).search("apm-*", body)
        return json.dumps(result, default=str, indent=2)

    @mcp.tool()
    async def apm_get_trace(trace_id: str, environment: str) -> str:
        """
        Get full trace details with all spans.

        Args:
            trace_id: Trace ID to retrieve
            environment: Target environment (dev, qa, uat, prod).
        """
        body = {
            "query": {"term": {"trace.id": trace_id}},
            "size": 1000,
            "sort": [{"@timestamp": {"order": "asc"}}],
        }
        result = await _client(environment).search("apm-*", body)
        return json.dumps(result, default=str, indent=2)

    @mcp.tool()
    async def apm_search_errors(
        environment: str,
        service_name: str = "",
        error_message: str = "",
        exception_type: str = "",
        hours_ago: int = 24,
        size: int = 10,
    ) -> str:
        """
        Search APM errors by service, message, or exception type.

        Args:
            environment: Target environment (dev, qa, uat, prod).
            service_name: Filter by service name (optional)
            error_message: Search in error message (optional)
            exception_type: Filter by exception type (optional)
            hours_ago: Search errors from this many hours ago (default: 24)
            size: Number of results to return (default: 10)
        """
        now = datetime.utcnow()
        start_time = now - timedelta(hours=hours_ago)
        must = [
            {"term": {"processor.event": "error"}},
            {"range": {"@timestamp": {"gte": start_time.isoformat(), "lte": now.isoformat()}}},
        ]
        if service_name:
            must.append({"term": {"service.name": service_name}})
        if error_message:
            must.append({"match": {"error.log.message": error_message}})
        if exception_type:
            must.append({"term": {"error.exception.type": exception_type}})
        body = {
            "query": {"bool": {"must": must}},
            "size": size,
            "sort": [{"@timestamp": {"order": "desc"}}],
        }
        result = await _client(environment).search("apm-*", body)
        return json.dumps(result, default=str, indent=2)

    @mcp.tool()
    async def apm_get_error(error_id: str, environment: str) -> str:
        """
        Get full error details with stack trace.

        Args:
            error_id: Error ID to retrieve
            environment: Target environment (dev, qa, uat, prod).
        """
        body = {"query": {"term": {"error.id": error_id}}}
        result = await _client(environment).search("apm-*", body)
        return json.dumps(result, default=str, indent=2)

    @mcp.tool()
    async def apm_list_services(environment: str, hours_ago: int = 1) -> str:
        """
        List all services with recent activity.

        Args:
            environment: Target environment (dev, qa, uat, prod).
            hours_ago: Look for services active in last N hours (default: 1)
        """
        now = datetime.utcnow()
        start_time = now - timedelta(hours=hours_ago)
        body = {
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": start_time.isoformat(), "lte": now.isoformat()}}},
                    ]
                }
            },
            "size": 0,
            "aggs": {"services": {"terms": {"field": "service.name", "size": 100}}},
        }
        result = await _client(environment).search("apm-*", body)
        return json.dumps(result, default=str, indent=2)

    @mcp.tool()
    async def apm_get_service_metrics(
        service_name: str, environment: str, hours_ago: int = 1
    ) -> str:
        """
        Get service metrics: throughput, latency, error rate.

        Args:
            service_name: Service name
            environment: Target environment (dev, qa, uat, prod).
            hours_ago: Analyze metrics from last N hours (default: 1)
        """
        now = datetime.utcnow()
        start_time = now - timedelta(hours=hours_ago)
        body = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"service.name": service_name}},
                        {"range": {"@timestamp": {"gte": start_time.isoformat(), "lte": now.isoformat()}}},
                    ]
                }
            },
            "size": 0,
            "aggs": {
                "transactions": {
                    "filter": {"term": {"processor.event": "transaction"}},
                    "aggs": {
                        "count": {"value_count": {"field": "transaction.id"}},
                        "avg_duration": {"avg": {"field": "transaction.duration.us"}},
                        "p95_duration": {"percentiles": {"field": "transaction.duration.us", "percents": [95]}},
                    },
                },
                "errors": {
                    "filter": {"term": {"processor.event": "error"}},
                    "aggs": {"count": {"value_count": {"field": "error.id"}}},
                },
            },
        }
        result = await _client(environment).search("apm-*", body)
        return json.dumps(result, default=str, indent=2)

    @mcp.tool()
    async def apm_find_slow_transactions(
        environment: str,
        service_name: str = "",
        min_duration_ms: int = 1000,
        hours_ago: int = 1,
        size: int = 10,
    ) -> str:
        """
        Find slow transactions exceeding duration threshold.

        Args:
            environment: Target environment (dev, qa, uat, prod).
            service_name: Filter by service name (optional)
            min_duration_ms: Minimum duration in milliseconds (default: 1000)
            hours_ago: Search from last N hours (default: 1)
            size: Number of results to return (default: 10)
        """
        now = datetime.utcnow()
        start_time = now - timedelta(hours=hours_ago)
        must = [
            {"term": {"processor.event": "transaction"}},
            {"range": {"@timestamp": {"gte": start_time.isoformat(), "lte": now.isoformat()}}},
            {"range": {"transaction.duration.us": {"gte": min_duration_ms * 1000}}},
        ]
        if service_name:
            must.append({"term": {"service.name": service_name}})
        body = {
            "query": {"bool": {"must": must}},
            "size": size,
            "sort": [{"transaction.duration.us": {"order": "desc"}}],
        }
        result = await _client(environment).search("apm-*", body)
        return json.dumps(result, default=str, indent=2)
