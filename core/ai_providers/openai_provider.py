from typing import Any, Dict, List

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
        return "gpt-4"

    async def generate_response(
        self, messages: List[Dict[str, str]], options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate response from OpenAI"""
        if options is None:
            options = {}

        model = options.get("model", self.default_model)
        max_tokens = options.get("maxTokens", 1000)
        temperature = options.get("temperature")

        request_params = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }

        if temperature is not None:
            request_params["temperature"] = temperature

        response = self._client.chat.completions.create(**request_params)

        return {
            "content": response.choices[0].message.content,
            "provider": "openai",
            "providerName": settings.OPENAI_BOT_NAME,
            "model": model,
            "usage": {
                "inputTokens": response.usage.prompt_tokens,
                "outputTokens": response.usage.completion_tokens,
                "totalTokens": response.usage.total_tokens,
            },
        }

    def is_available(self) -> bool:
        """Check if OpenAI provider is available"""
        return bool(self.api_key and self._client)
