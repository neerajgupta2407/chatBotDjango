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
        return settings.OPENAI_MODEL

    async def generate_response(
        self, messages: List[Dict[str, str]], options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate response from OpenAI"""
        if options is None:
            options = {}

        model = options.get("model") or self.default_model
        max_tokens = options.get("maxTokens", 30000)
        max_tokens = 30000
        temperature = options.get("temperature")

        # GPT-5 models require max_completion_tokens instead of max_tokens
        request_params = {
            "model": model,
            "messages": messages,
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
