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
import os
import sys
from pathlib import Path

from commons.constants import MCP_HTTP_URL, OPENAI_API_KEY, OPENAI_MODEL
from host.chat import run_mcp_agent
from host.mcp_clients.base import MCPClient
from host.mcp_clients.http import HttpMCPClient
from host.mcp_clients.stdio import StdioMCPClient


def build_mcp_client(transport: str) -> MCPClient:
    if transport == "http":
        return HttpMCPClient(mcp_server_url=MCP_HTTP_URL)
    if transport == "stdio":
        # The client launches the stdio server for us, using this same
        # interpreter so it shares our venv. The spawned process gets a minimal
        # environment by default, so we explicitly put the project root on
        # PYTHONPATH — otherwise `import servers`/`import commons` fail with
        # ModuleNotFoundError.
        project_root = Path(__file__).resolve().parent.parent
        env = {**os.environ, "PYTHONPATH": str(project_root)}
        return StdioMCPClient(
            command=sys.executable,
            args=["-m", "servers.stdio_server"],
            env=env,
        )
    raise ValueError(f"Unknown TRANSPORT: {transport!r}")


async def main():
    print("type `http` or `stdio` to connect to MCP server")
    user_input = input("\n> ").strip()
    await run_mcp_agent(
        build_mcp_client(user_input),
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        banner=f"MCP ({user_input}) agent is ready! Type your query or 'exit'.",
    )


if __name__ == "__main__":
    asyncio.run(main())
