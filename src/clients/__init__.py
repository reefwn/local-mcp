import httpx

from src.config import Config


class AtlassianClient:
    """Shared HTTP client for Atlassian Cloud APIs (Jira, Confluence)."""

    def __init__(self, config: Config):
        self.config = config
        self._client = httpx.AsyncClient(
            auth=(config.email, config.api_token),
            headers={"Accept": "application/json"},
            timeout=30.0,
        )

    async def jira_get(self, path: str, params: dict | None = None) -> dict:
        r = await self._client.get(f"{self.config.jira_base_url}{path}", params=params)
        r.raise_for_status()
        return r.json()

    async def jira_post(self, path: str, json: dict) -> dict:
        r = await self._client.post(f"{self.config.jira_base_url}{path}", json=json)
        r.raise_for_status()
        return r.json()

    async def confluence_get(self, path: str, params: dict | None = None) -> dict:
        r = await self._client.get(f"{self.config.confluence_base_url}{path}", params=params)
        r.raise_for_status()
        return r.json()

    async def bitbucket_get(self, path: str, params: dict | None = None) -> dict:
        r = await self._client.get(f"{self.config.bitbucket_base_url}{path}", params=params)
        r.raise_for_status()
        return r.json()

    async def close(self):
        await self._client.aclose()
