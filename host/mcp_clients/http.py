from contextlib import AsyncExitStack
from typing import Optional

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from host.mcp_clients.base import MCPClient


class HttpMCPClient(MCPClient):
    """Connects to an MCP server over Streamable HTTP.

    Optional ``headers`` are attached to every request — that single hook is
    all the auth-aware subclasses need (API key, OAuth Bearer token), which is
    why ``ApiKeyMCPClient`` and ``OauthMCPClient`` extend this class instead of
    duplicating the connection logic.

    The nested async context managers from the MCP SDK are driven through a
    single ``AsyncExitStack`` so they always unwind in the right order — even
    when the server rejects us (401/403), which keeps auth failures clean.
    """

    def __init__(self, mcp_server_url: str, headers: Optional[dict[str, str]] = None) -> None:
        super().__init__()
        self.mcp_server_url = mcp_server_url
        self.headers = headers or {}
        self._exit_stack: Optional[AsyncExitStack] = None

    async def _connect(self) -> None:
        """Open the HTTP streams + MCP session using the current ``headers``."""
        stack = AsyncExitStack()
        try:
            read_stream, write_stream, _ = await stack.enter_async_context(
                streamablehttp_client(self.mcp_server_url, headers=self.headers)
            )
            self.session = await stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            init_result = await self.session.initialize()
            print(init_result.model_dump_json(indent=2))
        except BaseException:
            await stack.aclose()
            self.session = None
            raise

        self._exit_stack = stack

    async def _disconnect(self) -> None:
        if self._exit_stack:
            await self._exit_stack.aclose()
            self._exit_stack = None
        self.session = None

    async def __aenter__(self):
        await self._connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._disconnect()
