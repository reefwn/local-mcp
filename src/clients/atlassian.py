import re

import httpx

from src.config import Config

_BITBUCKET_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


class BitbucketApiError(Exception):
    """Raised when the Bitbucket API returns an error. Message includes status, URL, and response body."""

    def __init__(self, response: httpx.Response):
        body = response.text.strip()
        self.status_code = response.status_code
        self.method = response.request.method
        self.url = str(response.request.url)
        self.body = body
        super().__init__(
            f"Bitbucket API error {response.status_code} {self.method} {self.url}\n{body or '(empty response body)'}"
        )


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


def format_bitbucket_uuid(value: str, *, label: str = "UUID") -> str:
    """Return a Bitbucket UUID path segment with braces. Raises ValueError if the value is not a valid UUID."""
    stripped = value.strip().strip("{}")
    if not stripped:
        raise ValueError(f"{label} is required (e.g. '{{6769c35b-a50d-4b4a-a1a9-35606d88c3b4}}').")
    if not _BITBUCKET_UUID_RE.match(stripped):
        raise ValueError(
            f"Invalid {label}: {value!r}. Expected a UUID like "
            f"'{{6769c35b-a50d-4b4a-a1a9-35606d88c3b4}}' (from bitbucket_list_pipeline_steps)."
        )
    return f"{{{stripped}}}"


def format_bitbucket_pipeline_ref(value: str) -> str:
    """Pipeline path segment: numeric build number as-is, otherwise a braced UUID. Raises ValueError if invalid."""
    stripped = value.strip()
    if not stripped:
        raise ValueError(
            "pipeline_uuid is required: use a build number (e.g. '263') or pipeline UUID from bitbucket_list_pipelines."
        )
    if stripped.isdigit():
        return stripped
    return format_bitbucket_uuid(stripped, label="pipeline_uuid")


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

    @staticmethod
    def _check_response(response: httpx.Response) -> None:
        if response.is_error:
            raise BitbucketApiError(response)

    async def get(self, path: str, params: dict | None = None) -> dict:
        r = await self._http.get(f"{self.config.bitbucket_base_url}{path}", params=params)
        self._check_response(r)
        return r.json()

    async def get_text(self, path: str, params: dict | None = None) -> str:
        r = await self._http.get(f"{self.config.bitbucket_base_url}{path}", params=params)
        self._check_response(r)
        return r.text

    async def get_binary_text(self, path: str) -> str:
        """GET a non-JSON resource (e.g. pipeline logs). Bitbucket returns 406 for Accept: application/json."""
        r = await self._http.get(
            f"{self.config.bitbucket_base_url}{path}",
            headers={"Accept": "*/*"},
        )
        if r.status_code == 406:
            raise BitbucketApiError(r)
        self._check_response(r)
        return r.text

    async def put(self, path: str, json: dict) -> dict:
        r = await self._http.put(f"{self.config.bitbucket_base_url}{path}", json=json)
        self._check_response(r)
        return r.json()

    async def post(self, path: str, json: dict) -> dict:
        r = await self._http.post(f"{self.config.bitbucket_base_url}{path}", json=json)
        self._check_response(r)
        return r.json()

    async def close(self) -> None:
        await self._http.aclose()
