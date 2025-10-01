from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseAIProvider(ABC):
    """Base class for AI providers"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name"""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return the default model for this provider"""
        pass

    @abstractmethod
    async def generate_response(
        self, messages: List[Dict[str, str]], options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate a response from the AI provider

        Args:
            messages: List of message dicts with 'role' and 'content'
            options: Optional configuration (model, temperature, max_tokens, etc.)

        Returns:
            Dict with keys: content, provider, providerName, model, usage
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and properly configured"""
        pass
