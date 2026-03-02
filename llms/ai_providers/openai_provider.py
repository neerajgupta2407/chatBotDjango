import json
from typing import Any, Dict, List, Optional

from django.conf import settings
from openai import OpenAI

from .base import BaseAIProvider


class OpenAIProvider(BaseAIProvider):
    """OpenAI GPT AI Provider"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self._client = OpenAI(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return settings.OPENAI_MODEL

    def _convert_tools(self, tools: List[Dict]) -> List[Dict]:
        """Convert tool definitions from our format to OpenAI function calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"],
                },
            }
            for tool in tools
        ]

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> List[Dict]:
        """Convert normalized messages to OpenAI API format.

        Handles:
        - Assistant messages with tool_calls → OpenAI tool_calls format
        - Tool result messages → role=tool with tool_call_id
        """
        openai_messages = []

        for msg in messages:
            role = msg.get("role", "")

            if role == "assistant" and "tool_calls" in msg:
                openai_messages.append(
                    {
                        "role": "assistant",
                        "content": msg.get("content") or None,
                        "tool_calls": [
                            {
                                "id": tc["id"],
                                "type": "function",
                                "function": {
                                    "name": tc["name"],
                                    "arguments": json.dumps(tc["input"]),
                                },
                            }
                            for tc in msg["tool_calls"]
                        ],
                    }
                )

            elif role == "tool":
                openai_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": msg["tool_call_id"],
                        "content": msg["content"],
                    }
                )

            else:
                openai_messages.append({"role": msg["role"], "content": msg["content"]})

        return openai_messages

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        options: Dict[str, Any] = None,
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Generate response from OpenAI"""
        if options is None:
            options = {}

        model = options.get("model") or self.default_model
        max_tokens = options.get("maxTokens", 1000)
        temperature = options.get("temperature")

        # Check if messages contain tool-related content
        has_tool_messages = tools or any(
            msg.get("role") == "tool" or "tool_calls" in msg for msg in messages
        )

        if has_tool_messages:
            converted_messages = self._convert_messages(messages)
        else:
            converted_messages = messages

        # GPT-5 models require max_completion_tokens instead of max_tokens
        request_params = {
            "model": model,
            "messages": converted_messages,
        }

        # Use max_completion_tokens for GPT-5 models, max_tokens for others
        if model.startswith("gpt-5"):
            request_params["max_completion_tokens"] = max_tokens
            # Set minimal reasoning effort to avoid empty responses
            request_params["reasoning_effort"] = "minimal"
        else:
            request_params["max_tokens"] = max_tokens

        if temperature is not None:
            request_params["temperature"] = temperature

        if tools:
            request_params["tools"] = self._convert_tools(tools)

        response = self._client.chat.completions.create(**request_params)

        message = response.choices[0].message

        result = {
            "content": message.content,
            "provider": "openai",
            "providerName": settings.OPENAI_BOT_NAME,
            "model": model,
            "usage": {
                "inputTokens": response.usage.prompt_tokens,
                "outputTokens": response.usage.completion_tokens,
                "totalTokens": response.usage.total_tokens,
            },
        }

        # Only check tool_calls when tools were provided
        if tools and message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "input": json.loads(tc.function.arguments),
                }
                for tc in message.tool_calls
            ]

        return result

    def is_available(self) -> bool:
        """Check if OpenAI provider is available"""
        return bool(self.api_key and self._client)
