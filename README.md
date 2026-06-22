# mcp-webinar

Materials for a webinar about **MCP (Model Context Protocol)**.

The project shows the *same* agent gaining tools five different ways, so you can
see exactly what MCP adds over hand-written tools — and how auth fits in.

| # | Demo | Host app | MCP server |
|---|------|----------|------------|
| 1 | Custom tools, no MCP | `host/app_custom_tools.py` | — |
| 2 | MCP over Streamable HTTP | `host/app_mcp_no_auth.py` (`TRANSPORT="http"`) | `servers/http_server.py` |
| 3 | MCP over stdio | `host/app_mcp_no_auth.py` (`TRANSPORT="stdio"`) | `servers/stdio_server.py` (auto-spawned) |
| 4 | MCP with API-key auth | `host/app_mcp_auth.py` (`AUTH="api_key"`) | `servers/api_key_mcp_server.py` |
| 5 | MCP with OAuth (Keycloak) | `host/app_mcp_auth.py` (`AUTH="oauth"`) | `servers/oauth_mcp_server.py` |

The agent always works against the **mock User Service** (search / read / create /
update / delete users).

## Architecture

```
commons/                 shared building blocks (no agent/MCP logic)
  constants.py           endpoints, ports, API key, system prompt
  user_service/          REST client + pydantic models for the mock service

host/                    the agent (OpenAI tool-calling) and its apps
  agent.py               ONE agent: takes list[BaseTool], streams, calls .execute()
  chat.py                shared REPL used by every app
  app_custom_tools.py    demo 1
  app_mcp_no_auth.py     demos 2 & 3 (toggle TRANSPORT)
  app_mcp_auth.py        demos 4 & 5 (toggle AUTH)
  tools/
    base.py              BaseTool: name/description/input_schema + .execute() + openai_schema
    mcp_tool.py          McpTool wraps a server tool; load_mcp_tools() discovers them
    users/               hand-written User Service tools (build_user_service_tools())
  mcp_clients/
    base.py              MCPClient: list_tools / call_tool / resources / prompts
    http.py              HttpMCPClient(url, headers) — base for the auth clients
    stdio.py             StdioMCPClient (local script or docker image)
    auth/
      api_key_mcp_client.py   ApiKeyMCPClient(HttpMCPClient) — adds X-API-Key
      oauth_mcp_client.py     OauthMCPClient(HttpMCPClient) — PKCE + token refresh
      _oauth_keycloak.py      OAuthTokenManager (browser PKCE flow)

servers/                 the MCP servers
  _server.py             the FastMCP instance + tools (shared by ALL servers)
  http_server.py         demo 2  (:8000/mcp)
  stdio_server.py        demo 3
  api_key_mcp_server.py  demo 4  (:8007/mcp)
  oauth_mcp_server.py    demo 5  (:8008/mcp)
  auth/                  API-key and JWT (Keycloak) middlewares
```

The key idea: **a tool is anything with an `execute()` method and an OpenAI
schema** (`BaseTool`). Hand-written `UserService*Tool`s and server-backed
`McpTool`s are interchangeable, so the agent and the chat loop never change —
only the list of tools handed to the agent does.

The servers never duplicate tool logic: every entrypoint imports the single
`mcp` instance from `servers/_server.py`; the auth servers just wrap it in a
middleware.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export OPENAI_API_KEY=sk-...          # required
# optional overrides: OPENAI_MODEL, MCP_API_KEY, *_URL (see commons/constants.py)

# mock User Service (all demos need it); Keycloak (only demo 5)
docker compose up -d userservice
```

Run every command below from the **repository root**.

### Demo 1 — custom tools
```bash
python -m host.app_custom_tools
```

### Demo 2 — MCP over HTTP
```bash
python -m servers.http_server          # terminal 1
python -m host.app_mcp_no_auth         # terminal 2  (TRANSPORT="http")
```

### Demo 3 — MCP over stdio
Set `TRANSPORT="stdio"` in `host/app_mcp_no_auth.py` (the server is spawned for you):
```bash
python -m host.app_mcp_no_auth
```

### Demo 4 — MCP with API key
```bash
python -m servers.api_key_mcp_server   # terminal 1
python -m host.app_mcp_auth            # terminal 2  (AUTH="api_key")
```

### Demo 5 — MCP with OAuth (Keycloak)
```bash
docker compose up -d keycloak
python -m servers.oauth_mcp_server     # terminal 1
# set AUTH="oauth" in host/app_mcp_auth.py
python -m host.app_mcp_auth            # terminal 2 — opens a browser to log in
```
Keycloak users (realm `mcp-realm`, see `docker-compose.yml`):
- `mcp-user` / `password` — has role `mcp-tools-access` ✅
- `no-access-user` / `password` — no role → server returns 403 ❌

> ⚠️ Access-token TTL is 60s on purpose, so you can demo the automatic refresh.

Type `exit` (or `quit`) to leave any chat.
