"""Streamable-HTTP MCP server behind a static API key (Demo 4).

    python -m servers.api_key_mcp_server   →  http://localhost:8007/mcp
"""
import uvicorn

from servers._server import create_mcp
from servers.auth.api_key_auth import APIKeyMiddleware

mcp = create_mcp()
app = mcp.http_app(path="/mcp", stateless_http=True)
app.add_middleware(APIKeyMiddleware)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8007, log_level="info")
