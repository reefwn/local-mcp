"""Streamable HTTP proxy to the official SonarQube MCP — injects server-side auth."""

from __future__ import annotations

import httpx
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.routing import Route

_HOP_BY_HOP = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }
)


def _response_headers(raw: httpx.Headers) -> dict[str, str]:
    return {
        key: value
        for key, value in raw.items()
        if key.lower() not in _HOP_BY_HOP
    }


def create_proxy_app(*, upstream_base: str, token: str) -> Starlette:
    base = upstream_base.rstrip("/")
    auth = f"Bearer {token}"

    async def forward(request: Request) -> Response:
        path = request.url.path or "/"
        url = f"{base}{path}"
        if request.url.query:
            url = f"{url}?{request.url.query}"

        headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in ("host", "authorization", "content-length")
        }
        headers["Authorization"] = auth
        body = await request.body()

        timeout = httpx.Timeout(300.0, connect=30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            upstream_req = httpx.Request(
                request.method,
                url,
                headers=headers,
                content=body if body else None,
            )
            upstream_resp = await client.send(upstream_req, stream=True)

            async def body_stream():
                try:
                    async for chunk in upstream_resp.aiter_bytes():
                        yield chunk
                finally:
                    await upstream_resp.aclose()

            return StreamingResponse(
                body_stream(),
                status_code=upstream_resp.status_code,
                headers=_response_headers(upstream_resp.headers),
            )

    methods = ["GET", "POST", "DELETE", "OPTIONS", "HEAD"]
    return Starlette(
        routes=[
            Route("/", forward, methods=methods),
            Route("/{path:path}", forward, methods=methods),
        ]
    )


async def run_proxy_server(*, host: str, port: int, upstream_base: str, token: str) -> None:
    app = create_proxy_app(upstream_base=upstream_base, token=token)
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
