import json
from collections import defaultdict

from openai import AsyncOpenAI

from host.models.message import Message
from host.models.role import Role
from host.tools.base import BaseTool


class Agent:

    def __init__(self, api_key: str, model: str, tools: list[BaseTool]):
        self.model = model
        self.tools = tools
        self._tools_by_name = {tool.name: tool for tool in tools}
        self._tool_schemas = [tool.openai_schema for tool in tools]
        self.openai = AsyncOpenAI(api_key=api_key)

    def _collect_tool_calls(self, tool_deltas):
        """Convert streaming tool call deltas to complete tool calls"""
        tool_dict = defaultdict(lambda: {"id": None, "function": {"arguments": "", "name": None}, "type": None})

        for delta in tool_deltas:
            idx = delta.index
            if delta.id: tool_dict[idx]["id"] = delta.id
            if delta.function.name: tool_dict[idx]["function"]["name"] = delta.function.name
            if delta.function.arguments: tool_dict[idx]["function"]["arguments"] += delta.function.arguments
            if delta.type: tool_dict[idx]["type"] = delta.type

        return list(tool_dict.values())

    async def _stream_response(self, messages: list[Message]) -> Message:
        """Stream an OpenAI response and capture any tool calls."""
        request: dict = {
            "model": self.model,
            "messages": [msg.to_dict() for msg in messages],
            "temperature": 0.0,
            "stream": True,
        }
        if self._tool_schemas:
            request["tools"] = self._tool_schemas

        stream = await self.openai.chat.completions.create(**request)

        content = ""
        tool_deltas = []

        print("🤖: ", end="", flush=True)

        async for chunk in stream:
            delta = chunk.choices[0].delta

            # Stream content
            if delta.content:
                print(delta.content, end="", flush=True)
                content += delta.content

            if delta.tool_calls:
                tool_deltas.extend(delta.tool_calls)

        print()
        return Message(
            role=Role.ASSISTANT,
            content=content,
            tool_calls=self._collect_tool_calls(tool_deltas) if tool_deltas else []
        )

    async def get_completion(self, messages: list[Message]) -> Message:
        """Process the conversation, streaming output and resolving tool calls."""
        ai_message: Message = await self._stream_response(messages)

        # Check if any tool calls are present and perform them
        if ai_message.tool_calls:
            messages.append(ai_message)
            await self._call_tools(ai_message, messages)
            # recursively calling agent with tool messages
            return await self.get_completion(messages)

        return ai_message

    async def _call_tools(self, ai_message: Message, messages: list[Message]):
        for tool_call in ai_message.tool_calls:
            tool_name = tool_call["function"]["name"]
            tool_args = json.loads(tool_call["function"]["arguments"])

            tool = self._tools_by_name.get(tool_name)
            if tool is None:
                result = f"Error: unknown tool '{tool_name}'"
                print(f"    ⚠️  {result}")
            else:
                try:
                    result = await tool.execute(tool_args)
                except Exception as e:
                    result = f"Error: {e}"
                    print(f"    ⚠️  {result}")

            messages.append(
                Message(
                    role=Role.TOOL,
                    content=str(result),
                    tool_call_id=tool_call["id"],
                )
            )
