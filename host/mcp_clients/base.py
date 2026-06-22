from abc import abstractmethod, ABC
from typing import Optional, Any

from mcp import ClientSession
from mcp.types import CallToolResult, TextContent, GetPromptResult, ReadResourceResult, Resource, TextResourceContents, BlobResourceContents, Prompt, Tool
from pydantic import AnyUrl


class MCPClient(ABC):
    """Transport-agnostic wrapper around an MCP ``ClientSession``.

    Subclasses implement the async-context-manager protocol to open a session
    over a specific transport (HTTP, stdio, API key, OAuth). Everything above
    the session — listing tools, calling tools, reading resources/prompts —
    is shared here.
    """

    def __init__(self) -> None:
        self.session: Optional[ClientSession] = None

    @abstractmethod
    async def __aenter__(self):
        ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        ...

    async def list_tools(self) -> list[Tool]:
        """Return the raw tool definitions advertised by the MCP server.

        Each ``Tool`` carries ``name``, ``description`` and ``inputSchema``.
        The host wraps these into ``McpTool`` objects (see
        ``host.tools.mcp_tool.load_mcp_tools``).
        """
        if not self.session:
            raise RuntimeError("MCP client not connected. Use 'async with' first.")

        result = await self.session.list_tools()
        return result.tools

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        """Call a specific tool on the MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected. Call connect() first.")

        print(f"    🔧 Calling `{tool_name}` with {tool_args}")

        tool_result: CallToolResult = await self.session.call_tool(tool_name, tool_args)

        if not tool_result.content:
            return "No content returned from tool"

        content = tool_result.content[0]
        print(f"    ⚙️: {content}\n")

        if isinstance(content, TextContent):
            return content.text

        return str(content)

    async def get_resources(self) -> list[Resource]:
        """Get available resources from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        try:
            result = await self.session.list_resources()
            return result.resources
        except Exception as e:
            print(f"Server doesn't support list_resources: {e}")
            return []

    async def get_resource(self, uri: AnyUrl) -> str:
        """Get specific resource content"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        resource_result: ReadResourceResult = await self.session.read_resource(uri)
        content = resource_result.contents[0]

        if isinstance(content, TextResourceContents):
            return content.text
        elif isinstance(content, BlobResourceContents):
            return content.blob
        raise ValueError(f"Unknown resource type for {uri}")

    async def get_prompts(self) -> list[Prompt]:
        """Get available prompts from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        try:
            result = await self.session.list_prompts()
            return result.prompts
        except Exception as e:
            print(f"Server doesn't support list_prompts: {e}")
            return []

    async def get_prompt(self, name: str) -> str:
        """Get specific prompt content"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        prompt_result: GetPromptResult = await self.session.get_prompt(name)

        combined_content = ""
        for message in prompt_result.messages:
            if hasattr(message, 'content') and isinstance(message.content, TextContent):
                combined_content += message.content.text + "\n"
            elif hasattr(message, 'content') and isinstance(message.content, str):
                combined_content += message.content + "\n"

        return combined_content.strip()