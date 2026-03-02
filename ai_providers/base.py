from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


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
        self,
        messages: List[Dict[str, Any]],
        options: Dict[str, Any] = None,
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a response from the AI provider

        Args:
            messages: List of message dicts with 'role' and 'content'.
                      May also contain tool-related messages:
                      - Assistant messages with 'tool_calls' key
                      - Tool result messages with role='tool', 'tool_call_id', 'name', 'content'
            options: Optional configuration (model, temperature, max_tokens, etc.)
            tools: Optional list of tool definitions for function calling.
                   Each tool has: name, description, input_schema

        Returns:
            Dict with keys: content, provider, providerName, model, usage
            When tools are used, may also include:
            - tool_calls: list of {id, name, input} dicts
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and properly configured"""
        pass
