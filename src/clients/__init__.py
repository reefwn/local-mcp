import httpx

from src.config import Config


class AtlassianClient:
    """Shared HTTP client for Atlassian Cloud APIs (Jira, Confluence)."""

    def __init__(self, config: Config):
        self.config = config
        common = {"headers": {"Accept": "application/json"}, "timeout": 30.0}
        self._jira = httpx.AsyncClient(auth=(config.jira_email, config.jira_api_token), **common)
        self._confluence = httpx.AsyncClient(auth=(config.confluence_email, config.confluence_api_token), **common)
        self._bitbucket = httpx.AsyncClient(auth=(config.bitbucket_email, config.bitbucket_api_token), **common)

    async def jira_get(self, path: str, params: dict | None = None) -> dict:
        r = await self._jira.get(f"{self.config.jira_base_url}{path}", params=params)
        r.raise_for_status()
        return r.json()

    async def jira_post(self, path: str, json: dict) -> dict:
        r = await self._jira.post(f"{self.config.jira_base_url}{path}", json=json)
        r.raise_for_status()
        return r.json()

    async def confluence_get(self, path: str, params: dict | None = None) -> dict:
        r = await self._confluence.get(f"{self.config.confluence_base_url}{path}", params=params)
        r.raise_for_status()
        return r.json()

    async def bitbucket_get(self, path: str, params: dict | None = None) -> dict:
        r = await self._bitbucket.get(f"{self.config.bitbucket_base_url}{path}", params=params)
        r.raise_for_status()
        return r.json()

    async def bitbucket_get_text(self, path: str, params: dict | None = None) -> str:
        r = await self._bitbucket.get(f"{self.config.bitbucket_base_url}{path}", params=params)
        r.raise_for_status()
        return r.text

    async def bitbucket_post(self, path: str, json: dict) -> dict:
        r = await self._bitbucket.post(f"{self.config.bitbucket_base_url}{path}", json=json)
        r.raise_for_status()
        return r.json()

    async def close(self):
        await self._jira.aclose()
        await self._confluence.aclose()
        await self._bitbucket.aclose()
