import os
import urllib.parse
from typing import Any

import httpx


class ObsidianClient:
    def __init__(self, api_key: str, base_url: str = "https://127.0.0.1:27124", verify_ssl: bool = False):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.verify_ssl = verify_ssl
        self.timeout = 6.0
        self._client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.api_key}"},
            verify=self.verify_ssl,
            timeout=self.timeout,
        )

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        try:
            response = await self._client.request(
                method,
                f"{self.base_url}{path}",
                **kwargs,
            )
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            raise Exception(f"Error {error_data.get('errorCode', -1)}: {error_data.get('message', '')}")
        except httpx.HTTPError as e:
            raise Exception(f"Request failed: {str(e)}")

    async def list_files_in_vault(self) -> list:
        r = await self._request("GET", "/vault/")
        return r.json()["files"]

    async def list_files_in_dir(self, dirpath: str) -> list:
        r = await self._request("GET", f"/vault/{dirpath}/")
        return r.json()["files"]

    async def get_file_contents(self, filepath: str) -> str:
        r = await self._request("GET", f"/vault/{filepath}")
        return r.text

    async def search(self, query: str, context_length: int = 100) -> Any:
        r = await self._request("POST", "/search/simple/", params={"query": query, "contextLength": context_length})
        return r.json()

    async def append_content(self, filepath: str, content: str) -> None:
        await self._request("POST", f"/vault/{filepath}", headers={"Content-Type": "text/markdown"}, content=content)

    async def patch_content(self, filepath: str, operation: str, target_type: str, target: str, content: str) -> None:
        await self._request(
            "PATCH",
            f"/vault/{filepath}",
            headers={
                "Content-Type": "text/markdown",
                "Operation": operation,
                "Target-Type": target_type,
                "Target": urllib.parse.quote(target),
            },
            content=content,
        )

    async def put_content(self, filepath: str, content: str) -> None:
        await self._request("PUT", f"/vault/{filepath}", headers={"Content-Type": "text/markdown"}, content=content)

    async def delete_file(self, filepath: str) -> None:
        await self._request("DELETE", f"/vault/{filepath}")

    async def search_json(self, query: dict) -> Any:
        r = await self._request(
            "POST", "/search/", headers={"Content-Type": "application/vnd.olrapi.jsonlogic+json"}, json=query
        )
        return r.json()

    async def get_periodic_note(self, period: str, type: str = "content") -> str:
        headers = {"Accept": "application/vnd.olrapi.note+json"} if type == "metadata" else {}
        r = await self._request("GET", f"/periodic/{period}/", headers=headers)
        return r.text

    async def get_recent_periodic_notes(self, period: str, limit: int = 5, include_content: bool = False) -> Any:
        r = await self._request(
            "GET", f"/periodic/{period}/recent", params={"limit": limit, "includeContent": include_content}
        )
        return r.json()

    async def get_recent_changes(self, limit: int = 10, days: int = 90) -> Any:
        dql_query = f"TABLE file.mtime\nWHERE file.mtime >= date(today) - dur({days} days)\nSORT file.mtime DESC\nLIMIT {limit}"
        r = await self._request(
            "POST", "/search/", headers={"Content-Type": "application/vnd.olrapi.dataview.dql+txt"}, content=dql_query.encode()
        )
        return r.json()
