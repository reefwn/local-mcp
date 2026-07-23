"""Aggregated, multi-environment Loki and Tempo debugging tools."""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Literal

import httpx
from mcp.server.fastmcp import FastMCP

from src.tools import loki_clients, tempo_clients

READ_ONLY_ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}


def _targets(clients: dict, environment: str, service: str) -> list[tuple[str, object]]:
    if environment == "all":
        targets = sorted(clients.items())
        if not targets:
            raise ValueError(f"No {service} clients are configured.")
        return targets

    client = clients.get(environment)
    if client is None:
        available = ", ".join(sorted(clients)) or "none"
        raise ValueError(
            f"No {service} client configured for environment '{environment}'. "
            f"Available environments: {available}."
        )
    return [(environment, client)]


def _time_range(hours_ago: int) -> tuple[datetime, datetime]:
    end = datetime.now(timezone.utc)
    return end - timedelta(hours=hours_ago), end


def _error_message(error: BaseException) -> str:
    if isinstance(error, httpx.HTTPStatusError):
        return f"HTTP {error.response.status_code} from the observability backend"
    if isinstance(error, httpx.TimeoutException):
        return "Observability backend request timed out"
    return f"Observability backend request failed ({type(error).__name__})"


async def _run_all(
    targets: list[tuple[str, object]],
    operation,
) -> tuple[list[tuple[str, dict]], dict[str, str]]:
    results = await asyncio.gather(
        *(operation(client) for _, client in targets),
        return_exceptions=True,
    )
    successes: list[tuple[str, dict]] = []
    errors: dict[str, str] = {}
    for (environment, _), result in zip(targets, results):
        if isinstance(result, BaseException):
            errors[environment] = _error_message(result)
        else:
            successes.append((environment, result))
    return successes, errors


def _iso_timestamp(timestamp_ns: str) -> str:
    try:
        return datetime.fromtimestamp(
            int(timestamp_ns) / 1_000_000_000,
            tz=timezone.utc,
        ).isoformat()
    except (TypeError, ValueError, OverflowError):
        return ""


def register_loki(mcp: FastMCP) -> None:
    @mcp.tool(
        name="loki_search_logs",
        annotations={"title": "Search Aggregated Loki Logs", **READ_ONLY_ANNOTATIONS},
    )
    async def loki_search_logs(
        query: str,
        environment: str = "all",
        hours_ago: int = 1,
        limit: int = 100,
        direction: Literal["backward", "forward"] = "backward",
    ) -> str:
        """Search Loki logs and merge results from all configured environments.

        Args:
            query: LogQL stream query, for example '{service_name="checkout"} |= "error"'.
            environment: dev, qa, uat, prod, or "all" (default) for an aggregated search.
            hours_ago: Search this many hours into the past (default: 1).
            limit: Maximum total merged log entries to return (default: 100).
            direction: "backward" for newest first or "forward" for oldest first.

        Returns:
            JSON with globally sorted entries, source environment, queried environments,
            and any per-environment errors.
        """
        if hours_ago < 1 or hours_ago > 720:
            raise ValueError("hours_ago must be between 1 and 720.")
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000.")

        start, end = _time_range(hours_ago)
        targets = _targets(loki_clients, environment, "loki")
        successes, errors = await _run_all(
            targets,
            lambda client: client.query_range(
                query,
                int(start.timestamp() * 1_000_000_000),
                int(end.timestamp() * 1_000_000_000),
                limit,
                direction,
            ),
        )

        entries = []
        for env, response in successes:
            for stream in response.get("data", {}).get("result", []):
                labels = stream.get("stream", {})
                for timestamp_ns, line in stream.get("values", []):
                    entries.append(
                        {
                            "environment": env,
                            "timestamp": _iso_timestamp(timestamp_ns),
                            "timestamp_ns": timestamp_ns,
                            "labels": labels,
                            "line": line,
                        }
                    )
        entries.sort(
            key=lambda entry: int(entry["timestamp_ns"]),
            reverse=direction == "backward",
        )
        entries = entries[:limit]
        return json.dumps(
            {
                "query": query,
                "environments": [env for env, _ in targets],
                "count": len(entries),
                "entries": entries,
                "errors": errors,
            },
            indent=2,
        )

    @mcp.tool(
        name="loki_list_labels",
        annotations={"title": "List Aggregated Loki Labels", **READ_ONLY_ANNOTATIONS},
    )
    async def loki_list_labels(
        environment: str = "all",
        hours_ago: int = 1,
    ) -> str:
        """List the union of Loki label names across configured environments."""
        if hours_ago < 1 or hours_ago > 720:
            raise ValueError("hours_ago must be between 1 and 720.")
        start, end = _time_range(hours_ago)
        targets = _targets(loki_clients, environment, "loki")
        successes, errors = await _run_all(
            targets,
            lambda client: client.labels(
                int(start.timestamp() * 1_000_000_000),
                int(end.timestamp() * 1_000_000_000),
            ),
        )
        by_environment = {
            env: sorted(response.get("data", [])) for env, response in successes
        }
        labels = sorted({label for values in by_environment.values() for label in values})
        return json.dumps(
            {
                "environments": [env for env, _ in targets],
                "labels": labels,
                "by_environment": by_environment,
                "errors": errors,
            },
            indent=2,
        )

    @mcp.tool(
        name="loki_list_label_values",
        annotations={"title": "List Aggregated Loki Label Values", **READ_ONLY_ANNOTATIONS},
    )
    async def loki_list_label_values(
        label: str,
        environment: str = "all",
        hours_ago: int = 1,
    ) -> str:
        """List the union of values for one Loki label across configured environments."""
        if hours_ago < 1 or hours_ago > 720:
            raise ValueError("hours_ago must be between 1 and 720.")
        start, end = _time_range(hours_ago)
        targets = _targets(loki_clients, environment, "loki")
        successes, errors = await _run_all(
            targets,
            lambda client: client.label_values(
                label,
                int(start.timestamp() * 1_000_000_000),
                int(end.timestamp() * 1_000_000_000),
            ),
        )
        by_environment = {
            env: sorted(response.get("data", [])) for env, response in successes
        }
        values = sorted({value for items in by_environment.values() for value in items})
        return json.dumps(
            {
                "label": label,
                "environments": [env for env, _ in targets],
                "values": values,
                "by_environment": by_environment,
                "errors": errors,
            },
            indent=2,
        )


def register_tempo(mcp: FastMCP) -> None:
    @mcp.tool(
        name="tempo_search_traces",
        annotations={"title": "Search Aggregated Tempo Traces", **READ_ONLY_ANNOTATIONS},
    )
    async def tempo_search_traces(
        query: str = "{}",
        environment: str = "all",
        hours_ago: int = 1,
        limit: int = 20,
    ) -> str:
        """Search Tempo with TraceQL and merge traces from all configured environments."""
        if hours_ago < 1 or hours_ago > 720:
            raise ValueError("hours_ago must be between 1 and 720.")
        if limit < 1 or limit > 200:
            raise ValueError("limit must be between 1 and 200.")
        start, end = _time_range(hours_ago)
        targets = _targets(tempo_clients, environment, "tempo")
        successes, errors = await _run_all(
            targets,
            lambda client: client.search(
                query,
                int(start.timestamp()),
                int(end.timestamp()),
                limit,
            ),
        )
        traces = []
        for env, response in successes:
            for trace in response.get("traces", []):
                traces.append({"environment": env, **trace})
        traces.sort(
            key=lambda trace: int(trace.get("startTimeUnixNano", 0)),
            reverse=True,
        )
        traces = traces[:limit]
        return json.dumps(
            {
                "query": query,
                "environments": [env for env, _ in targets],
                "count": len(traces),
                "traces": traces,
                "errors": errors,
            },
            indent=2,
        )

    @mcp.tool(
        name="tempo_get_trace",
        annotations={"title": "Get Tempo Trace", **READ_ONLY_ANNOTATIONS},
    )
    async def tempo_get_trace(
        trace_id: str,
        environment: str = "all",
    ) -> str:
        """Retrieve a trace by ID from one or every configured Tempo environment."""
        targets = _targets(tempo_clients, environment, "tempo")
        successes, errors = await _run_all(
            targets,
            lambda client: client.get_trace(trace_id),
        )
        return json.dumps(
            {
                "trace_id": trace_id,
                "environments": [env for env, _ in targets],
                "matches": [
                    {"environment": env, "trace": response}
                    for env, response in successes
                ],
                "errors": errors,
            },
            indent=2,
        )

    @mcp.tool(
        name="tempo_list_services",
        annotations={"title": "List Aggregated Tempo Services", **READ_ONLY_ANNOTATIONS},
    )
    async def tempo_list_services(
        environment: str = "all",
        hours_ago: int = 1,
        limit: int = 100,
    ) -> str:
        """List the union of services observed in Tempo across configured environments."""
        if hours_ago < 1 or hours_ago > 720:
            raise ValueError("hours_ago must be between 1 and 720.")
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000.")
        start, end = _time_range(hours_ago)
        targets = _targets(tempo_clients, environment, "tempo")
        successes, errors = await _run_all(
            targets,
            lambda client: client.tag_values(
                "resource.service.name",
                int(start.timestamp()),
                int(end.timestamp()),
                limit,
            ),
        )
        by_environment = {
            env: sorted(
                item.get("value", "")
                for item in response.get("tagValues", [])
                if item.get("value")
            )
            for env, response in successes
        }
        services = sorted(
            {service for values in by_environment.values() for service in values}
        )
        return json.dumps(
            {
                "environments": [env for env, _ in targets],
                "services": services,
                "by_environment": by_environment,
                "errors": errors,
            },
            indent=2,
        )
