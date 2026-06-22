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

The agent always works against the **[mock User Service](https://github.com/khshanovskyi/mock-user-service)** (search / read / create /
update / delete users).


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

---

### Demo 2 — MCP over HTTP
```bash
python -m servers.http_server          # terminal 1
python -m host.app_mcp_no_auth         # terminal 2  (TRANSPORT="http")
```

---

### Demo 3 — MCP over stdio
Set `TRANSPORT="stdio"` in `host/app_mcp_no_auth.py` (the server is spawned for you):

```bash
python -m host.app_mcp_no_auth         # choose "stdio" when prompted
```

<details> 
<summary><b>Connecting your STDIO MCP server to Claude Desktop</b></summary>

This uses your `servers/stdio_server.py` entry point — simplest and most reliable for local development.

### Step 1: Find the Claude Desktop config file

| OS          | Path                                                              |
|-------------|-------------------------------------------------------------------|
| **macOS**   | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json`                     |

### Step 2: Edit the config

Open the file (create it if it doesn't exist) and add your server:

```json
{
  "mcpServers": {
    "users-management": {
      "command": "{ABSOLUTE_PATH}/mcp-webinar/.venv/bin/python",
      "args": [
        "{ABSOLUTE_PATH}/mcp-webinar/servers/stdio_server.py"
      ],
      "env": {
        "PYTHONPATH": "{ABSOLUTE_PATH}/mcp-webinar"
      }
    }
  }
}
```

**Important notes:**

- Don't forget to replace `{ABSOLUTE_PATH}` with the absolute path to the project on your local machine
- Set `PYTHONPATH` to your project root so imports like `servers` and `commons` resolve correctly
- If you're using a virtual environment, point to its Python binary:
  ```json
  "command": "/path/to/your/venv/bin/python"
  ```
  On Windows: `"C:\\Users\\you\\project\\.venv\\Scripts\\python.exe"`

<details> 
<summary><b>Sample how it is done on my Mac:</b></summary>

```json
{
  "mcpServers": {
    "users-management": {
      "command": "/Users/pavlokhshanovskyi/my-courses/mcp-webinar/.venv/bin/python",
      "args": [
        "/Users/pavlokhshanovskyi/my-courses/mcp-webinar/servers/stdio_server.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/pavlokhshanovskyi/my-courses/mcp-webinar"
      }
    }
  }
}
```

![claude_stdio.gif](claude_stdio.gif)
</details>

### Step 3: Restart Claude Desktop

Fully quit and reopen Claude Desktop. While reopening, Claude can ask for access to the project. In the connectors section you will be able to find `users-management`.

</details>

---

### Demo 4 — MCP with API key
```bash
python -m servers.api_key_mcp_server   # terminal 1
python -m host.app_mcp_auth            # terminal 2  (AUTH="api_key")
```

---

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
