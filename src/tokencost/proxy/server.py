"""HTTP proxy server for intercepting and logging LLM API calls.

Uses an async architecture with httpx.AsyncClient for efficient
non-blocking request forwarding to upstream LLM providers.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from tokencost.pricing.models import calculate_cost, get_model_pricing
from tokencost.tracker.database import log_call

PROVIDER_HOSTS: dict[str, str] = {
    "api.openai.com": "openai",
    "api.anthropic.com": "anthropic",
}


def _parse_usage(provider: str, body: dict[str, Any]) -> tuple[str, int, int]:
    """Parse model name and token usage from an API response body.

    Args:
        provider: The API provider name ('openai', 'anthropic', etc.).
        body: The parsed JSON response body.

    Returns:
        A tuple of (model_name, input_tokens, output_tokens).
    """
    model = body.get("model", "unknown")
    if provider == "openai":
        usage = body.get("usage", {})
        return model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
    elif provider == "anthropic":
        usage = body.get("usage", {})
        return model, usage.get("input_tokens", 0), usage.get("output_tokens", 0)
    return model, 0, 0


def _log_response(target_host: str, resp_body: bytes) -> None:
    """Parse and log API usage from a response body.

    Args:
        target_host: The upstream API host that was called.
        resp_body: The raw response body bytes.
    """
    provider = PROVIDER_HOSTS.get(target_host, "unknown")
    try:
        resp_json = json.loads(resp_body)
        model, input_tokens, output_tokens = _parse_usage(provider, resp_json)
        if input_tokens > 0 or output_tokens > 0:
            pricing = get_model_pricing(model)
            if pricing:
                cost = calculate_cost(model, input_tokens, output_tokens)
                log_call(provider, model, input_tokens, output_tokens, cost)
                print(f"[{model}] input:{input_tokens} output:{output_tokens} cost:${cost:.4f}")
    except (json.JSONDecodeError, ValueError):
        pass


async def _handle_request(
    scope: dict[str, Any],
    receive: Any,
    send: Any,
    client: httpx.AsyncClient,
    target_host: str,
) -> None:
    """Handle a single ASGI HTTP request by proxying to the target host.

    Args:
        scope: The ASGI connection scope.
        receive: The ASGI receive callable.
        send: The ASGI send callable.
        client: The shared async HTTP client.
        target_host: The upstream API host to proxy to.
    """
    # Read request body
    body = b""
    while True:
        message = await receive()
        body += message.get("body", b"")
        if not message.get("more_body", False):
            break

    # Build target URL
    path = scope.get("path", "/")
    query = scope.get("query_string", b"")
    url = f"https://{target_host}{path}"
    if query:
        url += f"?{query.decode()}"

    # Forward headers (skip hop-by-hop)
    headers: dict[str, str] = {}
    for raw_name, raw_value in scope.get("headers", []):
        name = raw_name.decode("latin-1").lower()
        if name not in ("host", "transfer-encoding"):
            headers[name] = raw_value.decode("latin-1")

    method = scope.get("method", "POST")
    resp = await client.request(method, url, headers=headers, content=body)

    # Log usage
    if method == "POST":
        _log_response(target_host, resp.content)

    # Send response
    resp_headers = [
        (k.encode(), v.encode())
        for k, v in resp.headers.items()
        if k.lower() not in ("transfer-encoding", "content-encoding")
    ]
    resp_headers.append((b"content-length", str(len(resp.content)).encode()))

    await send(
        {
            "type": "http.response.start",
            "status": resp.status_code,
            "headers": resp_headers,
        }
    )
    await send({"type": "http.response.body", "body": resp.content})


def _make_asgi_app(target_host: str) -> Any:
    """Create an ASGI application that proxies requests to a target host.

    Args:
        target_host: The upstream API host (e.g., 'api.openai.com').

    Returns:
        An ASGI application callable.
    """
    client = httpx.AsyncClient(timeout=120.0)

    async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] == "http":
            await _handle_request(scope, receive, send, client, target_host)

    return app


def run_proxy(port: int = 8800, host: str = "127.0.0.1") -> None:
    """Run the transparent proxy server.

    Starts an async HTTP server that intercepts API calls to LLM providers,
    logs token usage and costs, then forwards requests to the real API.

    Args:
        port: Port number to listen on.
        host: Host address to bind to.
    """
    try:
        import uvicorn
    except ImportError:
        # Fallback: use a simple asyncio-based server
        _run_simple_proxy(port, host)
        return

    print(f"🔌 TokenCost proxy running on {host}:{port}")
    print(f"Set OPENAI_API_BASE=http://127.0.0.1:{port}/v1 to route through proxy")
    app = _make_asgi_app("api.openai.com")
    uvicorn.run(app, host=host, port=port, log_level="warning")


def _run_simple_proxy(port: int, host: str) -> None:
    """Run a simple async proxy server without uvicorn.

    Uses asyncio and httpx.AsyncClient directly with a minimal HTTP server.

    Args:
        port: Port number to listen on.
        host: Host address to bind to.
    """
    from http.server import BaseHTTPRequestHandler, HTTPServer

    target_host = "api.openai.com"
    loop = asyncio.new_event_loop()
    client = httpx.AsyncClient(timeout=120.0)

    class ProxyHandler(BaseHTTPRequestHandler):
        """HTTP request handler that proxies to LLM APIs."""

        def do_POST(self) -> None:
            """Handle POST requests by forwarding to the upstream API."""
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else None

            url = f"https://{target_host}{self.path}"
            fwd_headers: dict[str, str] = {}
            for key, val in self.headers.items():
                if key.lower() not in ("host", "transfer-encoding"):
                    fwd_headers[key] = val

            async def forward() -> tuple[int, dict[str, str], bytes]:
                resp = await client.request("POST", url, headers=fwd_headers, content=body)
                return resp.status_code, dict(resp.headers), resp.content

            status, resp_headers, resp_body = loop.run_until_complete(forward())
            _log_response(target_host, resp_body)

            self.send_response(status)
            for key, val in resp_headers.items():
                if key.lower() not in ("transfer-encoding", "content-encoding", "content-length"):
                    self.send_header(key, val)
            self.send_header("Content-Length", str(len(resp_body)))
            self.end_headers()
            self.wfile.write(resp_body)

        def log_message(self, format: str, *args: object) -> None:
            """Suppress default HTTP server logging."""

    server = HTTPServer((host, port), ProxyHandler)
    print(f"🔌 TokenCost proxy running on {host}:{port}")
    print(f"Set OPENAI_API_BASE=http://127.0.0.1:{port}/v1 to route through proxy")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nProxy stopped.")
        server.server_close()
    finally:
        loop.run_until_complete(client.aclose())
        loop.close()
