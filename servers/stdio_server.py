"""stdio MCP server (Demo 3).

Not started manually — the host's stdio client spawns it via
`python -m servers.stdio_server` and talks to it over stdin/stdout.
"""
from servers._server import create_mcp

if __name__ == "__main__":
    create_mcp().run(transport="stdio")
