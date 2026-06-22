from typing import Any

from host.mcp_clients.auth._oauth_keycloak import OAuthTokenManager
from host.mcp_clients.http import HttpMCPClient


class OauthMCPClient(HttpMCPClient):
    """MCP client that authenticates via OAuth 2.0 + PKCE (Keycloak).

    On ``__aenter__``:
      1. Runs the PKCE browser flow (opens the Keycloak login once)
      2. Connects to the MCP server with the resulting Bearer token

    On every tool call:
      - If the access token is about to expire, it is refreshed and the MCP
        session is re-established with the new token. (Keycloak's access-token
        TTL in this demo is only 60s, so this path is easy to show live.)
    """

    def __init__(self, mcp_server_url: str) -> None:
        super().__init__(mcp_server_url=mcp_server_url)
        self.token_manager = OAuthTokenManager()

    async def __aenter__(self):
        # Step 1: browser-based PKCE login → access + refresh tokens.
        await self.token_manager.authenticate()
        # Step 2: connect using the Bearer header (stored on self.headers).
        self.headers = await self.token_manager.auth_headers()
        await self._connect()
        return self

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        if self.token_manager.is_token_expired():
            print("    🔄 Token expired — refreshing and reconnecting...")
            await self._reconnect_with_fresh_token()

        return await super().call_tool(tool_name, tool_args)

    async def _reconnect_with_fresh_token(self) -> None:
        """Refresh the OAuth token and rebuild the MCP session with it."""
        await self.token_manager.refresh()
        await self._disconnect()
        self.headers = await self.token_manager.auth_headers()
        await self._connect()
        print("    ✅ Reconnected with fresh token")
