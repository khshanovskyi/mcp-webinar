"""Streamable-HTTP MCP server behind Keycloak OAuth (Demo 5).

    docker compose up -d keycloak
    python -m servers.oauth_mcp_server   →  http://localhost:8008/mcp
"""
import uvicorn

from servers._server import mcp
from servers.auth.oauth import JWTAuthMiddleware

app = mcp.streamable_http_app()
app.add_middleware(JWTAuthMiddleware)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008, log_level="info")
