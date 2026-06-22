from host.mcp_clients.http import HttpMCPClient


class ApiKeyMCPClient(HttpMCPClient):
    """MCP client that authenticates with a static API key.

    The key is sent on every request via the ``X-API-Key`` header, which the
    server validates in ``servers/auth/api_key_auth.py``. Apart from that
    header, the connection is identical to a plain HTTP client — so all the
    transport logic is inherited from ``HttpMCPClient``.
    """

    def __init__(self, mcp_server_url: str, api_key: str) -> None:
        super().__init__(
            mcp_server_url=mcp_server_url,
            headers={"X-API-Key": api_key},
        )
