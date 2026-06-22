"""Demos 2 & 3 — Agent with MCP tools, no auth.

The exact same agent, but the tools now come from an MCP server instead of
being hand-written. Flip ``TRANSPORT`` to switch between:

  * "http"  — Streamable HTTP server (Demo 2). Start it first:
                python -m servers.http_server
  * "stdio" — stdio server (Demo 3). The client spawns it automatically.

Run:
    docker compose up -d userservice
    export OPENAI_API_KEY=sk-...
    python -m host.app_mcp_no_auth
"""
import asyncio
import sys

from commons.constants import MCP_HTTP_URL, OPENAI_API_KEY, OPENAI_MODEL
from host.chat import run_mcp_agent
from host.mcp_clients.http import HttpMCPClient
from host.mcp_clients.stdio import StdioMCPClient

# ── Choose the transport for the demo ───────────────────────────────────────
TRANSPORT = "http"  # "http" or "stdio"


def build_mcp_client():
    if TRANSPORT == "http":
        return HttpMCPClient(mcp_server_url=MCP_HTTP_URL)
    if TRANSPORT == "stdio":
        # The client launches the stdio server for us, using this same
        # interpreter so it shares our venv.
        return StdioMCPClient(command=sys.executable, args=["-m", "servers.stdio_server"])
    raise ValueError(f"Unknown TRANSPORT: {TRANSPORT!r}")


async def main():
    await run_mcp_agent(
        build_mcp_client(),
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        banner=f"MCP ({TRANSPORT}) agent is ready! Type your query or 'exit'.",
    )


if __name__ == "__main__":
    asyncio.run(main())
