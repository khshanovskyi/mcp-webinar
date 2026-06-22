"""Thin host-facing adapter over ``fastmcp.Client``.

``fastmcp`` already gives us a fully-featured MCP client — transport inference,
session lifecycle, OAuth (PKCE + browser + token refresh), and typed
tools/resources/prompts. This module is the small shim that keeps the host's
existing interface intact: ``call_tool`` returns a plain ``str`` (what
``McpTool.execute`` expects), prompts/resources degrade gracefully on servers
that don't support them, and one ``capabilities`` property feeds the banner.

The ``build_*`` helpers construct the right transport/auth so the app entry
points stay declarative.
"""
from typing import Any, Optional

from fastmcp import Client
from fastmcp.client.auth import OAuth
from fastmcp.client.transports import StdioTransport, StreamableHttpTransport
from mcp.types import (
    BlobResourceContents,
    Prompt,
    Resource,
    TextContent,
    TextResourceContents,
    Tool,
)
from pydantic import AnyUrl


class MCPClient:
    """Transport-agnostic wrapper around a ``fastmcp.Client``.

    Construct one with the ``build_*`` helpers below, then use it as an async
    context manager::

        async with build_http(url) as client:
            tools = await client.list_tools()
    """

    def __init__(self, client: Client) -> None:
        self._client = client

    async def __aenter__(self) -> "MCPClient":
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._client.__aexit__(exc_type, exc_val, exc_tb)

    @property
    def capabilities(self):
        """Server capabilities negotiated during initialization (or ``None``)."""
        result = self._client.initialize_result
        return result.capabilities if result else None

    async def list_tools(self) -> list[Tool]:
        """Return the raw tool definitions advertised by the MCP server.

        Each ``Tool`` carries ``name``, ``description`` and ``inputSchema`` —
        the host wraps these into ``McpTool`` objects (see
        ``host.tools.mcp_tool.load_mcp_tools``).
        """
        return await self._client.list_tools()

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        """Call a tool and flatten the result to text for the agent."""
        print(f"    🔧 Calling `{tool_name}` with {tool_args}")

        result = await self._client.call_tool(tool_name, tool_args)

        if not result.content:
            return "No content returned from tool"

        content = result.content[0]
        print(f"    ⚙️: {content}\n")

        if isinstance(content, TextContent):
            return content.text

        return str(content)

    async def get_resources(self) -> list[Resource]:
        """Get available resources from MCP server (``[]`` if unsupported)."""
        try:
            return await self._client.list_resources()
        except Exception as e:
            print(f"Server doesn't support list_resources: {e}")
            return []

    async def get_resource(self, uri: AnyUrl) -> str:
        """Get specific resource content."""
        contents = await self._client.read_resource(uri)
        content = contents[0]

        if isinstance(content, TextResourceContents):
            return content.text
        elif isinstance(content, BlobResourceContents):
            return content.blob
        raise ValueError(f"Unknown resource type for {uri}")

    async def get_prompts(self) -> list[Prompt]:
        """Get available prompts from MCP server (``[]`` if unsupported)."""
        try:
            return await self._client.list_prompts()
        except Exception as e:
            print(f"Server doesn't support list_prompts: {e}")
            return []

    async def get_prompt(self, name: str) -> str:
        """Get specific prompt content."""
        prompt_result = await self._client.get_prompt(name)

        combined_content = ""
        for message in prompt_result.messages:
            if hasattr(message, "content") and isinstance(message.content, TextContent):
                combined_content += message.content.text + "\n"
            elif hasattr(message, "content") and isinstance(message.content, str):
                combined_content += message.content + "\n"

        return combined_content.strip()


# ==================== TRANSPORT / AUTH BUILDERS ====================

def build_http(url: str, headers: Optional[dict[str, str]] = None) -> MCPClient:
    """Plain Streamable-HTTP MCP client."""
    return MCPClient(Client(StreamableHttpTransport(url, headers=headers)))


def build_stdio(
    command: str,
    args: list[str],
    env: Optional[dict[str, str]] = None,
) -> MCPClient:
    """Local stdio MCP client — the server process is spawned for you."""
    return MCPClient(Client(StdioTransport(command=command, args=args, env=env)))


def build_docker(image: str, env: Optional[dict[str, str]] = None) -> MCPClient:
    """stdio MCP client that launches the server as a Docker container."""
    return MCPClient(
        Client(StdioTransport(command="docker", args=["run", "--rm", "-i", image], env=env))
    )


def build_api_key(url: str, api_key: str) -> MCPClient:
    """HTTP client that authenticates with a static ``X-API-Key`` header."""
    return MCPClient(Client(StreamableHttpTransport(url, headers={"X-API-Key": api_key})))


def build_oauth(url: str, client_id: str = "mcp-client", callback_port: int = 9999) -> MCPClient:
    """OAuth 2.0 client following the MCP Authorization spec.

    ``fastmcp``'s ``OAuth`` helper discovers the authorization server from the
    MCP server's protected-resource metadata, runs the PKCE browser flow, and
    transparently refreshes tokens. ``client_id`` is passed explicitly because
    our Keycloak realm has Dynamic Client Registration disabled — we reuse the
    pre-registered public client. ``callback_port`` matches the redirect URI
    registered for that client (``http://localhost:9999/*``).
    """
    return MCPClient(
        Client(url, auth=OAuth(mcp_url=url, client_id=client_id, callback_port=callback_port))
    )
