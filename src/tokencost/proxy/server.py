"""HTTP proxy server for intercepting and logging LLM API calls."""

from __future__ import annotations

import asyncio
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx

from tokencost.pricing.models import calculate_cost, get_model_pricing
from tokencost.tracker.database import log_call

PROVIDER_HOSTS = {
    "api.openai.com": "openai",
    "api.anthropic.com": "anthropic",
}


def _parse_usage(provider: str, body: dict) -> tuple[str, int, int]:
    """Parse model and token usage from response body."""
    model = body.get("model", "unknown")
    if provider == "openai":
        usage = body.get("usage", {})
        return model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
    elif provider == "anthropic":
        usage = body.get("usage", {})
        return model, usage.get("input_tokens", 0), usage.get("output_tokens", 0)
    return model, 0, 0


async def _forward_request(
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes | None,
) -> tuple[int, dict[str, str], bytes]:
    """Forward a request to the real API and return the response."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.request(method, url, headers=headers, content=body)
        return resp.status_code, dict(resp.headers), resp.content


def _make_handler(target_host: str) -> type[BaseHTTPRequestHandler]:
    """Create a request handler class for proxying to a specific host."""

    class ProxyHandler(BaseHTTPRequestHandler):
        """HTTP request handler that proxies to LLM APIs."""

        def do_POST(self) -> None:
            """Handle POST requests (main API call method)."""
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else None

            # Build target URL
            url = f"https://{target_host}{self.path}"

            # Forward headers (skip hop-by-hop)
            fwd_headers = {}
            for key, val in self.headers.items():
                if key.lower() not in ("host", "transfer-encoding"):
                    fwd_headers[key] = val

            # Forward request
            loop = asyncio.new_event_loop()
            try:
                status, resp_headers, resp_body = loop.run_until_complete(
                    _forward_request("POST", url, fwd_headers, body)
                )
            finally:
                loop.close()

            # Try to parse and log
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

            # Send response
            self.send_response(status)
            for key, val in resp_headers.items():
                if key.lower() not in ("transfer-encoding", "content-encoding", "content-length"):
                    self.send_header(key, val)
            self.send_header("Content-Length", str(len(resp_body)))
            self.end_headers()
            self.wfile.write(resp_body)

        def log_message(self, format: str, *args: object) -> None:
            """Suppress default logging."""

    return ProxyHandler


def run_proxy(port: int = 8800, host: str = "127.0.0.1") -> None:
    """Run the proxy server."""
    # Simple approach: proxy to OpenAI by default, detect from request
    handler = _make_handler("api.openai.com")
    server = HTTPServer((host, port), handler)
    print(f"🔌 TokenCost proxy running on {host}:{port}")
    print("Set OPENAI_API_BASE=http://127.0.0.1:{port}/v1 to route through proxy")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nProxy stopped.")
        server.server_close()
