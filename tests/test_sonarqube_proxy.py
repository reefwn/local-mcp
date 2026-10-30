from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from starlette.testclient import TestClient

from src.sonarqube_proxy import create_proxy_app


def test_proxy_injects_bearer_token():
    captured: dict[str, str | None] = {}

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = httpx.Headers({"content-type": "text/plain"})

    async def aiter_bytes():
        yield b"ok"

    mock_resp.aiter_bytes = aiter_bytes
    mock_resp.aclose = AsyncMock()

    async def fake_send(request, stream=True):
        captured["auth"] = request.headers.get("Authorization")
        return mock_resp

    mock_client = MagicMock()
    mock_client.send = AsyncMock(side_effect=fake_send)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    app = create_proxy_app(upstream_base="http://sonar-backend", token="squ_secret")
    with patch("src.sonarqube_proxy.httpx.AsyncClient", return_value=mock_client):
        client = TestClient(app)
        response = client.get("/health")

    assert response.status_code == 200
    assert captured["auth"] == "Bearer squ_secret"
