import httpx


class ElasticsearchClient:
    """Async Elasticsearch client."""

    def __init__(self, url: str, api_key: str = "", username: str = "", password: str = ""):
        self._url = url.rstrip("/")
        self._api_key = api_key
        self._username = username
        self._password = password
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {}
            auth = None
            
            if self._api_key:
                headers["Authorization"] = f"ApiKey {self._api_key}"
            elif self._username and self._password:
                auth = (self._username, self._password)
            
            self._client = httpx.AsyncClient(
                base_url=self._url,
                headers=headers,
                auth=auth,
                timeout=30.0,
            )
        return self._client

    async def search(self, index: str, body: dict) -> dict:
        """Execute a search query."""
        resp = await self._get_client().post(f"/{index}/_search", json=body)
        resp.raise_for_status()
        return resp.json()

    async def get_document(self, index: str, doc_id: str) -> dict:
        """Get a document by ID."""
        resp = await self._get_client().get(f"/{index}/_doc/{doc_id}")
        resp.raise_for_status()
        return resp.json()

    async def list_indices(self) -> list[dict]:
        """List all indices with stats."""
        resp = await self._get_client().get("/_cat/indices?format=json&bytes=b")
        resp.raise_for_status()
        return resp.json()

    async def get_mapping(self, index: str) -> dict:
        """Get field mappings for an index."""
        resp = await self._get_client().get(f"/{index}/_mapping")
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        if self._client:
            await self._client.aclose()
