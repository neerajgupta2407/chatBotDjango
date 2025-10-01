from typing import Any, Dict, List, Optional

from django.conf import settings

from .anthropic_provider import AnthropicProvider
from .base import BaseAIProvider
from .dummy_provider import DummyProvider
from .openai_provider import OpenAIProvider


class AIProviderFactory:
    """Factory class for managing AI providers (Claude, OpenAI, and Dummy)"""

    _instance = None
    _providers: Dict[str, BaseAIProvider] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_providers()
        return cls._instance

    def _initialize_providers(self):
        """Initialize AI providers based on available API keys"""
        # Initialize Claude
        if settings.ANTHROPIC_API_KEY:
            self._providers["claude"] = AnthropicProvider(
                api_key=settings.ANTHROPIC_API_KEY
            )

        # Initialize OpenAI
        if settings.OPENAI_API_KEY:
            self._providers["openai"] = OpenAIProvider(api_key=settings.OPENAI_API_KEY)

        # Initialize Dummy (always available)
        if getattr(settings, "ENABLE_DUMMY_PROVIDER", False):
            self._providers["dummy"] = DummyProvider()

    def get_provider(self, provider_name: Optional[str] = None) -> BaseAIProvider:
        """Get AI provider instance"""
        name = provider_name or settings.AI_PROVIDER

        if name not in self._providers:
            raise ValueError(
                f"AI provider '{name}' is not available. "
                f"Check your API keys. Available providers: {list(self._providers.keys())}"
            )

        return self._providers[name]

    async def generate_response(
        self,
        provider_name: Optional[str],
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate response from specified AI provider"""
        if options is None:
            options = {}

        name = provider_name or settings.AI_PROVIDER
        provider = self.get_provider(name)

        return await provider.generate_response(messages, options)

    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return list(self._providers.keys())

    def is_provider_available(self, provider_name: str) -> bool:
        """Check if a provider is available"""
        return provider_name in self._providers


# Singleton instance
ai_provider = AIProviderFactory()
