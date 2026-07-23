"""Async clients for Grafana Loki and Tempo query APIs."""

from urllib.parse import quote

import httpx


class _GrafanaQueryClient:
    """Shared authentication and HTTP behavior for Grafana query services."""

    def __init__(
        self,
        url: str,
        token: str = "",
        username: str = "",
        password: str = "",
        tenant_id: str = "",
    ):
        self._url = url.rstrip("/")
        self._token = token
        self._username = username
        self._password = password
        self._tenant_id = tenant_id
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {"Accept": "application/json"}
            auth = None
            if self._tenant_id:
                headers["X-Scope-OrgID"] = self._tenant_id
            if self._token:
                headers["Authorization"] = f"Bearer {self._token}"
            elif self._username and self._password:
                auth = (self._username, self._password)
            self._client = httpx.AsyncClient(
                base_url=self._url,
                headers=headers,
                auth=auth,
                timeout=30.0,
            )
        return self._client

    async def _get(self, path: str, params: dict | None = None) -> dict:
        response = await self._get_client().get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


class LokiClient(_GrafanaQueryClient):
    """Query Grafana Loki through its stable HTTP API."""

    async def query_range(
        self,
        query: str,
        start_ns: int,
        end_ns: int,
        limit: int,
        direction: str,
    ) -> dict:
        return await self._get(
            "/loki/api/v1/query_range",
            {
                "query": query,
                "start": str(start_ns),
                "end": str(end_ns),
                "limit": limit,
                "direction": direction,
            },
        )

    async def labels(self, start_ns: int, end_ns: int) -> dict:
        return await self._get(
            "/loki/api/v1/labels",
            {"start": str(start_ns), "end": str(end_ns)},
        )

    async def label_values(self, label: str, start_ns: int, end_ns: int) -> dict:
        encoded_label = quote(label, safe="")
        return await self._get(
            f"/loki/api/v1/label/{encoded_label}/values",
            {"start": str(start_ns), "end": str(end_ns)},
        )


class TempoClient(_GrafanaQueryClient):
    """Query Grafana Tempo through its stable HTTP API."""

    async def search(
        self,
        query: str,
        start_s: int,
        end_s: int,
        limit: int,
    ) -> dict:
        return await self._get(
            "/api/search",
            {
                "q": query,
                "start": start_s,
                "end": end_s,
                "limit": limit,
            },
        )

    async def get_trace(self, trace_id: str) -> dict:
        encoded_trace_id = quote(trace_id, safe="")
        return await self._get(f"/api/v2/traces/{encoded_trace_id}")

    async def tag_values(
        self,
        tag: str,
        start_s: int,
        end_s: int,
        limit: int,
        query: str = "",
    ) -> dict:
        encoded_tag = quote(tag, safe=".")
        params: dict[str, str | int] = {
            "start": start_s,
            "end": end_s,
            "limit": limit,
        }
        if query:
            params["q"] = query
        return await self._get(
            f"/api/v2/search/tag/{encoded_tag}/values",
            params,
        )
