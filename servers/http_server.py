"""Streamable-HTTP MCP server WITHOUT auth (Demo 2).

    python -m servers.http_server   →  http://localhost:8000/mcp
"""
import uvicorn

from servers._server import create_mcp

mcp = create_mcp()
app = mcp.http_app(path="/mcp", stateless_http=False)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
