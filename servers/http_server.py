"""Streamable-HTTP MCP server WITHOUT auth (Demo 2).

    python -m servers.http_server   →  http://localhost:8000/mcp
"""
import uvicorn

from servers._server import mcp

app = mcp.streamable_http_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
