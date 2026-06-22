"""Demos 4 & 5 — Agent with authenticated MCP tools.

Same agent again — only the MCP client changes to carry credentials. Flip
``AUTH`` to switch between:

  * "api_key" — static API key in the X-API-Key header (Demo 4). Start:
                  python -m servers.api_key_mcp_server
  * "oauth"   — OAuth 2.0 + PKCE via Keycloak (Demo 5). Start:
                  docker compose up -d keycloak
                  python -m servers.oauth_mcp_server
                A browser window opens for login (user: mcp-user / password).

Run:
    docker compose up -d userservice
    export OPENAI_API_KEY=sk-...
    python -m host.app_mcp_auth
"""
import asyncio

from commons.constants import (
    MCP_API_KEY,
    MCP_API_KEY_URL,
    MCP_OAUTH_URL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)
from host.chat import run_mcp_agent
from host.mcp_client import build_api_key, build_oauth

# ── Choose the auth scheme for the demo ─────────────────────────────────────
AUTH = "oauth"  # "api_key" or "oauth"


def build_mcp_client():
    if AUTH == "api_key":
        return build_api_key(MCP_API_KEY_URL, MCP_API_KEY)
    if AUTH == "oauth":
        return build_oauth(MCP_OAUTH_URL)
    raise ValueError(f"Unknown AUTH: {AUTH!r}")


async def main():
    await run_mcp_agent(
        build_mcp_client(),
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        banner=f"MCP ({AUTH}) agent is ready! Type your query or 'exit'.",
    )


if __name__ == "__main__":
    asyncio.run(main())
