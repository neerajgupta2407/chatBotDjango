from typing import Any, Dict, List, Optional

from anthropic import Anthropic
from django.conf import settings

from .base import BaseAIProvider


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude AI Provider"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self._client = Anthropic(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return "claude"

    @property
    def default_model(self) -> str:
        return settings.CLAUDE_MODEL

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> tuple:
        """Convert normalized messages to Anthropic API format.

        Handles:
        - System messages → extracted to separate system parameter
        - Assistant messages with tool_calls → content blocks with tool_use
        - Tool result messages → user messages with tool_result content blocks

        Returns:
            Tuple of (system_prompt or None, converted_messages)
        """
        system_prompt = None
        anthropic_messages = []

        for msg in messages:
            role = msg.get("role", "")

            if role == "system":
                system_prompt = msg["content"]

            elif role == "assistant" and "tool_calls" in msg:
                content = []
                if msg.get("content"):
                    content.append({"type": "text", "text": msg["content"]})
                for tc in msg["tool_calls"]:
                    content.append(
                        {
                            "type": "tool_use",
                            "id": tc["id"],
                            "name": tc["name"],
                            "input": tc["input"],
                        }
                    )
                anthropic_messages.append({"role": "assistant", "content": content})

            elif role == "tool":
                tool_result = {
                    "type": "tool_result",
                    "tool_use_id": msg["tool_call_id"],
                    "content": msg["content"],
                }
                # Group consecutive tool results into a single user message
                if (
                    anthropic_messages
                    and anthropic_messages[-1]["role"] == "user"
                    and isinstance(anthropic_messages[-1]["content"], list)
                    and anthropic_messages[-1]["content"]
                    and anthropic_messages[-1]["content"][0].get("type")
                    == "tool_result"
                ):
                    anthropic_messages[-1]["content"].append(tool_result)
                else:
                    anthropic_messages.append(
                        {"role": "user", "content": [tool_result]}
                    )

            else:
                anthropic_messages.append({"role": role, "content": msg["content"]})

        return system_prompt, anthropic_messages

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        options: Dict[str, Any] = None,
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Generate response from Claude"""
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
            system_prompt, converted_messages = self._convert_messages(messages)
        else:
            system_prompt = None
            converted_messages = messages

        request_params = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": converted_messages,
        }

        if system_prompt:
            request_params["system"] = system_prompt

        if temperature is not None:
            request_params["temperature"] = temperature

        if tools:
            request_params["tools"] = tools

        response = self._client.messages.create(**request_params)

        # When tools are provided, iterate content blocks to find tool_use
        if tools:
            text_content = ""
            tool_calls = []
            for block in response.content:
                if getattr(block, "type", None) == "text":
                    text_content += block.text
                elif getattr(block, "type", None) == "tool_use":
                    tool_calls.append(
                        {
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        }
                    )

            result = {
                "content": text_content or None,
                "provider": "claude",
                "providerName": settings.CLAUDE_BOT_NAME,
                "model": model,
                "usage": {
                    "inputTokens": response.usage.input_tokens,
                    "outputTokens": response.usage.output_tokens,
                },
            }

            if tool_calls:
                result["tool_calls"] = tool_calls

            return result

        # Simple path (no tools) — backward compatible
        return {
            "content": response.content[0].text,
            "provider": "claude",
            "providerName": settings.CLAUDE_BOT_NAME,
            "model": model,
            "usage": {
                "inputTokens": response.usage.input_tokens,
                "outputTokens": response.usage.output_tokens,
            },
        }

    def is_available(self) -> bool:
        """Check if Anthropic provider is available"""
        return bool(self.api_key and self._client)
