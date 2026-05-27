import httpx

from src.config import Config


class JiraCloudClient:
    """Atlassian Cloud APIs for Jira and Confluence (same site domain, shared credentials)."""

    def __init__(self, config: Config):
        self.config = config
        common = {"headers": {"Accept": "application/json"}, "timeout": 30.0}
        jira_auth = (config.jira_email, config.jira_api_token)
        self._jira = httpx.AsyncClient(auth=jira_auth, **common)

        confluence_email = config.confluence_email or config.jira_email
        confluence_token = config.confluence_api_token or config.jira_api_token
        confluence_auth = (confluence_email, confluence_token)
        if confluence_auth == jira_auth:
            self._confluence = self._jira
        else:
            self._confluence = httpx.AsyncClient(auth=confluence_auth, **common)

    async def jira_get(self, path: str, params: dict | None = None) -> dict:
        r = await self._jira.get(f"{self.config.jira_base_url}{path}", params=params)
        r.raise_for_status()
        return r.json()

    async def jira_post(self, path: str, json: dict) -> dict:
        r = await self._jira.post(f"{self.config.jira_base_url}{path}", json=json)
        r.raise_for_status()
        return r.json() if r.content else {}

    async def jira_put(self, path: str, json: dict) -> None:
        r = await self._jira.put(f"{self.config.jira_base_url}{path}", json=json)
        r.raise_for_status()

    async def confluence_get(self, path: str, params: dict | None = None) -> dict:
        r = await self._confluence.get(f"{self.config.confluence_base_url}{path}", params=params)
        r.raise_for_status()
        return r.json()

    async def close(self) -> None:
        await self._jira.aclose()
        if self._confluence is not self._jira:
            await self._confluence.aclose()


class BitbucketClient:
    """Bitbucket Cloud API (separate credentials from Jira/Confluence)."""

    def __init__(self, config: Config):
        self.config = config
        common = {"headers": {"Accept": "application/json"}, "timeout": 30.0}
        self._http = httpx.AsyncClient(
            auth=(config.bitbucket_email, config.bitbucket_api_token),
            follow_redirects=True,
            **common,
        )

    async def get(self, path: str, params: dict | None = None) -> dict:
        r = await self._http.get(f"{self.config.bitbucket_base_url}{path}", params=params)
        r.raise_for_status()
        return r.json()

    async def get_text(self, path: str, params: dict | None = None) -> str:
        r = await self._http.get(f"{self.config.bitbucket_base_url}{path}", params=params)
        r.raise_for_status()
        return r.text

    async def put(self, path: str, json: dict) -> dict:
        r = await self._http.put(f"{self.config.bitbucket_base_url}{path}", json=json)
        r.raise_for_status()
        return r.json()

    async def post(self, path: str, json: dict) -> dict:
        r = await self._http.post(f"{self.config.bitbucket_base_url}{path}", json=json)
        r.raise_for_status()
        return r.json()

    async def close(self) -> None:
        await self._http.aclose()
