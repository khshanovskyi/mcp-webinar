"""Streamable-HTTP MCP server behind Keycloak OAuth (Demo 5).

Follows the MCP Authorization spec: the server is an OAuth **Resource Server**.
``RemoteAuthProvider`` makes FastMCP automatically serve
``/.well-known/oauth-protected-resource`` and answer unauthenticated requests
with a ``401`` + ``WWW-Authenticate: Bearer resource_metadata=...`` challenge.
The client discovers Keycloak from that metadata and logs in itself — no
endpoints are hardcoded on the client.

``JWTVerifier`` validates the Bearer token's signature against Keycloak's JWKS,
checks the issuer, and requires the ``mcp-tools-access`` scope (surfaced into
the token's ``scp`` claim by a Keycloak protocol mapper — see
``_keycloak/mcp-realm-config.json``).

    docker compose up -d keycloak
    python -m servers.oauth_mcp_server   →  http://localhost:8008/mcp
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

ISSUER = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"
JWKS_URL = f"{ISSUER}/protocol/openid-connect/certs"

# ==================== AUTH PROVIDER ====================

# Validates Keycloak-issued JWTs (signature via JWKS, issuer, required scope).
# audience is intentionally not enforced — matches the previous demo's setup.
# The required "scope" is satisfied by the Keycloak realm role of the same name
# (see servers/auth/oauth.py).
token_verifier = KeycloakRoleScopeVerifier(
    jwks_uri=JWKS_URL,
    issuer=ISSUER,
    required_scopes=[REQUIRED_SCOPE],
)

# Resource Server: advertises Keycloak as the authorization server and serves
# the protected-resource metadata the client uses for discovery.
#
# scopes_supported is what the client will REQUEST from Keycloak during the
# authorize step, so it must list real Keycloak scopes (standard OIDC ones).
# It deliberately does NOT include "mcp-tools-access": that is a Keycloak realm
# role, not a requestable client scope (Keycloak would reject it with
# "invalid_scope"). Authorization on that role is enforced server-side by
# KeycloakRoleScopeVerifier, which reads it from the token's realm_access.roles
# — the role rides along automatically via Keycloak's default "roles" scope.
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
