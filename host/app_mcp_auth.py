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
    GITHUB_MCP_URL,
    GITHUB_MCP_API_KEY,
)
from host.chat import run_mcp_agent
from host.mcp_client import build_api_key, build_oauth


def build_mcp_client(auth: str):
    if auth == "api_key":
        # GitHub connection with API Key
        return build_api_key(
            url=GITHUB_MCP_URL,
            api_key=GITHUB_MCP_API_KEY,
            header_name="Authorization"
        )
        # return build_api_key(
        #     url=MCP_API_KEY_URL,
        #     api_key=MCP_API_KEY,
        #     header_name="Authorization"
        # )
    if auth == "oauth":
        return build_oauth(MCP_OAUTH_URL)
    raise ValueError(f"Unknown AUTH: {auth!r}")


async def main():
    print("type `oauth` or `api_key` to choose MCP server Auth approach")
    auth = input("\n> ").strip()
    await run_mcp_agent(
        build_mcp_client(auth),
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        banner=f"MCP ({auth}) agent is ready! Type your query or 'exit'.",
    )


if __name__ == "__main__":
    asyncio.run(main())
