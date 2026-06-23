import os

# ── OpenAI ────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")

# ── Mock User Service (docker-compose) ──────────────────────────────────────
USER_SERVICE_ENDPOINT = os.getenv("USER_SERVICE_ENDPOINT", "http://localhost:8041")

# ── MCP servers ─────────────────────────────────────────────────────────────
# Streamable-HTTP MCP server without auth (servers/http_server.py)
MCP_HTTP_URL = os.getenv("MCP_HTTP_URL", "http://localhost:8000/mcp")
# Streamable-HTTP MCP server behind an API key (servers/api_key_mcp_server.py)
MCP_API_KEY_URL = os.getenv("MCP_API_KEY_URL", "http://localhost:8007/mcp")
# Streamable-HTTP MCP server behind Keycloak OAuth (servers/oauth_mcp_server.py)
MCP_OAUTH_URL = os.getenv("MCP_OAUTH_URL", "http://localhost:8008/mcp")

# GitHub with API Key (PAT)
GITHUB_MCP_URL="https://api.githubcopilot.com/mcp/"
GITHUB_MCP_API_KEY=f"Bearer {os.getenv("GITHUB_MCP_KEY", "wrong")}"

# Shared secret expected by the API-key server / sent by the API-key client.
MCP_API_KEY = os.getenv("MCP_API_KEY", "dev-secret-key")

# ── Agent ───────────────────────────────────────────────────────────────────
DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful assistant for managing users in a user-management system. "
    "You can search, read, create, update and delete users by calling the tools "
    "available to you. Always use a tool when the user asks about users instead of "
    "guessing. When you show a user, present the information clearly. Ask for "
    "confirmation before deleting a user."
)
