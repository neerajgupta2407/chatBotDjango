from typing import Any, Dict, List

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

    async def generate_response(
        self, messages: List[Dict[str, str]], options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate response from Claude"""
        if options is None:
            options = {}

        model = options.get("model") or self.default_model
        max_tokens = options.get("maxTokens", 1000)
        temperature = options.get("temperature")

        request_params = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }

        if temperature is not None:
            request_params["temperature"] = temperature

        response = self._client.messages.create(**request_params)

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
