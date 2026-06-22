"""Token verification for the OAuth (Keycloak) MCP server.

The MCP Authorization flow itself (discovery, metadata, the ``WWW-Authenticate``
challenge) is handled by ``fastmcp``'s ``RemoteAuthProvider`` in
``servers/oauth_mcp_server.py``. This module only customises how an incoming
Bearer token is *authorized*.

``fastmcp``'s ``JWTVerifier`` already validates the token's signature (against
Keycloak's JWKS), issuer and expiry, and can enforce ``required_scopes``. The
only wrinkle: it reads scopes from the standard ``scope`` claim, but Keycloak
expresses access via **realm roles** (``realm_access.roles``), not scopes.

``KeycloakRoleScopeVerifier`` bridges that gap by treating the user's realm
roles as additional scopes — so ``required_scopes=["mcp-tools-access"]`` is
satisfied iff the user has the matching realm role. ``mcp-user`` (granted the
role) passes; ``no-access-user`` (no role) is rejected with a 401. No Keycloak
realm changes are needed.
"""
from typing import Any

from fastmcp.server.auth.providers.jwt import JWTVerifier


class KeycloakRoleScopeVerifier(JWTVerifier):
    """JWTVerifier that also counts Keycloak realm roles as scopes."""

    def _extract_scopes(self, claims: dict[str, Any]) -> list[str]:
        scopes = list(super()._extract_scopes(claims))
        realm_roles = (claims.get("realm_access") or {}).get("roles") or []
        return scopes + list(realm_roles)
