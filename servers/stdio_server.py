"""stdio MCP server (Demo 3).

Not started manually — the host's StdioMCPClient spawns it via
`python -m servers.stdio_server` and talks to it over stdin/stdout.
"""
from servers._server import mcp

if __name__ == "__main__":
    mcp.run(transport="stdio")
