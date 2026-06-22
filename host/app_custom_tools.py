"""Demo 1 — Agent with hand-written tools (no MCP).

The agent talks to the mock User Service directly through Python tools we wrote
ourselves. This is the baseline: every tool is custom code living inside the
host. Compare it with the MCP demos to see what MCP buys you.

Run:
    docker compose up -d userservice
    export OPENAI_API_KEY=sk-...
    python -m host.app_custom_tools
"""
import asyncio

from commons.constants import OPENAI_API_KEY, OPENAI_MODEL
from commons.user_service.client import UserServiceClient
from host.agent import Agent
from host.chat import print_tools, run_chat_loop
from host.tools.base import BaseTool
from host.tools.users.create_user_tool import CreateUserTool
from host.tools.users.delete_user_tool import DeleteUserTool
from host.tools.users.get_user_by_id_tool import GetUserByIdTool
from host.tools.users.search_users_tool import SearchUsersTool
from host.tools.users.update_user_tool import UpdateUserTool


async def main():
    user_client = UserServiceClient()
    tools: list[BaseTool] = [
        GetUserByIdTool(user_client),
        SearchUsersTool(user_client),
        CreateUserTool(user_client),
        UpdateUserTool(user_client),
        DeleteUserTool(user_client),
    ]
    print_tools(tools)

    agent = Agent(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        tools=tools,
    )

    await run_chat_loop(agent, banner="Custom-tools agent is ready! Type your query or 'exit'.")


if __name__ == "__main__":
    asyncio.run(main())
