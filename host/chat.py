import json

import httpx

from commons.constants import DEFAULT_SYSTEM_PROMPT
from host.agent import Agent
from host.mcp_clients.base import MCPClient
from host.models.message import Message
from host.models.role import Role
from host.tools.base import BaseTool
from host.tools.mcp_tool import load_mcp_tools


def print_tools(tools: list[BaseTool]) -> None:
    """Pretty-print the OpenAI schema of every tool the agent will expose."""
    print("\n=== Available Tools ===")
    for tool in tools:
        print(json.dumps(tool.openai_schema, indent=2))


def print_prompts(prompts: list) -> None:
    """Pretty-print the prompts advertised by the MCP server."""
    print("\n=== Available Prompts ===")
    if not prompts:
        print("(none)")
        return
    for prompt in prompts:
        print(prompt.model_dump_json(indent=2))


def print_resources(resources: list) -> None:
    """Pretty-print the resources advertised by the MCP server."""
    print("\n=== Available Resources ===")
    if not resources:
        print("(none)")
        return
    for resource in resources:
        print(resource.model_dump_json(indent=2))


def print_server_capabilities(mcp_client: MCPClient) -> None:
    """Pretty-print the capabilities negotiated with the MCP server."""
    print("\n=== MCP Server Capabilities ===")
    capabilities = mcp_client.session.get_server_capabilities() if mcp_client.session else None
    if capabilities is None:
        print("(unavailable)")
        return
    print(capabilities.model_dump_json(indent=2))


async def run_chat_loop(agent: Agent, banner: str) -> None:
    """Interactive REPL shared by all demos.

    Keeps a single conversation, forwards user input to the agent, and lets the
    agent stream its answer and call tools as needed. Type 'exit' to quit.
    """
    messages: list[Message] = [
        Message(role=Role.SYSTEM, content=DEFAULT_SYSTEM_PROMPT)
    ]

    print(banner)
    while True:
        user_input = input("\n> ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue

        messages.append(Message(role=Role.USER, content=user_input))

        ai_message: Message = await agent.get_completion(messages)
        messages.append(ai_message)


async def run_mcp_agent(mcp_client: MCPClient, api_key: str, model: str, banner: str) -> None:
    """Connect to an MCP server, expose its tools to the agent, and chat.

    Shared by the no-auth and the authenticated MCP demos — only the client
    handed in differs. Auth rejections (HTTP 401/403) are reported cleanly
    instead of dumping a stack trace, so the OAuth/API-key demos stay readable.
    """
    try:
        async with mcp_client:
            print_server_capabilities(mcp_client)

            tools = await load_mcp_tools(mcp_client)
            print_tools(tools)

            prompts = await mcp_client.get_prompts()
            print_prompts(prompts)

            resources = await mcp_client.get_resources()
            print_resources(resources)

            agent = Agent(api_key=api_key, model=model, tools=tools)
            await run_chat_loop(agent, banner)
    except Exception as exc:
        http_error = _find_http_status_error(exc)
        if http_error is None:
            raise
        response = http_error.response
        print(
            f"\n❌ MCP server rejected the request: HTTP {response.status_code} "
            f"{response.reason_phrase}.\n"
            f"   Check your credentials/role and that the server is running."
        )


def _find_http_status_error(exc: BaseException) -> httpx.HTTPStatusError | None:
    """Dig an ``httpx.HTTPStatusError`` out of a (possibly grouped) exception."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc
    if isinstance(exc, BaseExceptionGroup):
        for sub in exc.exceptions:
            found = _find_http_status_error(sub)
            if found is not None:
                return found
    return None
