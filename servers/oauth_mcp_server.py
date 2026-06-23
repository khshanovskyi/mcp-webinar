"""
Streamable-HTTP MCP server behind Keycloak OAuth (Demo 5).
"""
import os

import uvicorn
from fastmcp.server.auth import RemoteAuthProvider

from servers._server import create_mcp
from servers.auth.oauth import KeycloakRoleScopeVerifier

# ==================== CONFIGURATION ====================

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8089")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "mcp-realm")
REQUIRED_SCOPE = os.getenv("MCP_REQUIRED_SCOPE", "mcp-tools-access")
SERVER_BASE_URL = os.getenv("MCP_OAUTH_BASE_URL", "http://localhost:8008")
MCP_RESOURCE_URL = os.getenv("MCP_OAUTH_RESOURCE", f"{SERVER_BASE_URL}/mcp")

ISSUER = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"
JWKS_URL = f"{ISSUER}/protocol/openid-connect/certs"

# ==================== AUTH PROVIDER ====================

token_verifier = KeycloakRoleScopeVerifier(
    jwks_uri=JWKS_URL,
    issuer=ISSUER,
    audience=MCP_RESOURCE_URL,
    required_scopes=[REQUIRED_SCOPE],
)

auth = RemoteAuthProvider(
    token_verifier=token_verifier,
    authorization_servers=[ISSUER],
    base_url=SERVER_BASE_URL,
    scopes_supported=["openid", "profile", "email"],
)

mcp = create_mcp(auth=auth)
app = mcp.http_app(path="/mcp", stateless_http=True)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008, log_level="info")
