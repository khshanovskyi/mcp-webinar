from typing import Any

from host.mcp_clients.client import MCPClient
from host.tools.base import BaseTool


class McpTool(BaseTool):
    """A ``BaseTool`` that proxies its execution to a tool living on an MCP server.

    The agent treats it exactly like a hand-written tool: it has a ``name``,
    a ``description`` and an ``input_schema`` (all advertised by the server),
    and an ``execute`` method. Calling ``execute`` forwards the arguments to
    the MCP server over whatever transport the ``mcp_client`` uses (HTTP,
    stdio, API key, OAuth, …).
    """

    def __init__(
        self,
        mcp_client: MCPClient,
        name: str,
        description: str,
        input_schema: dict[str, Any],
    ) -> None:
        self._mcp_client = mcp_client
        self._name = name
        self._description = description
        self._input_schema = input_schema

    async def execute(self, arguments: dict[str, Any]) -> str:
        return await self._mcp_client.call_tool(self._name, arguments)

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def input_schema(self) -> dict[str, Any]:
        return self._input_schema


async def load_mcp_tools(mcp_client: MCPClient) -> list[McpTool]:
    """Discover the tools exposed by an MCP server and wrap each as an ``McpTool``.

    This is the bridge between the MCP world and the agent: the agent only
    knows about ``BaseTool`` objects, so we ask the server for its tool list
    (name, description, JSON-Schema) and turn every entry into something the
    agent can schedule and execute.
    """
    tools = await mcp_client.list_tools()
    return [
        McpTool(
            mcp_client=mcp_client,
            name=tool.name,
            description=tool.description or "",
            input_schema=tool.inputSchema,
        )
        for tool in tools
    ]
