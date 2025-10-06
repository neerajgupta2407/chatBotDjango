import random
from typing import Any, Dict, List

from django.conf import settings

from .base import BaseAIProvider


class DummyProvider(BaseAIProvider):
    """Dummy LLM Provider for testing and development"""

    def __init__(self, api_key: str = "dummy-key"):
        super().__init__(api_key)
        self._client = True  # Mock client

    @property
    def provider_name(self) -> str:
        return "dummy"

    @property
    def default_model(self) -> str:
        return settings.DUMMY_MODEL

    async def generate_response(
        self, messages: List[Dict[str, str]], options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate a mock response"""
        if options is None:
            options = {}

        model = options.get("model") or self.default_model

        # Get the last user message
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        last_message = user_messages[-1]["content"] if user_messages else ""

        # Generate dummy response based on message content
        response_content = self._generate_dummy_content(last_message)

        # Mock token counts
        input_tokens = sum(len(msg.get("content", "").split()) for msg in messages)
        output_tokens = len(response_content.split())

        return {
            "content": response_content,
            "provider": "dummy",
            "providerName": getattr(settings, "DUMMY_BOT_NAME", "Dummy Assistant"),
            "model": model,
            "usage": {
                "inputTokens": input_tokens,
                "outputTokens": output_tokens,
                "totalTokens": input_tokens + output_tokens,
            },
        }

    def _generate_dummy_content(self, user_message: str) -> str:
        """Generate contextual dummy responses"""
        message_lower = user_message.lower()

        # Contextual responses
        if "hello" in message_lower or "hi" in message_lower:
            responses = [
                "Hello! I'm a dummy AI assistant. How can I help you today?",
                "Hi there! This is a dummy response for testing purposes.",
                "Greetings! I'm simulating an AI response.",
            ]
        elif "how are you" in message_lower:
            responses = [
                "I'm just a dummy AI, but I'm functioning perfectly!",
                "As a dummy provider, I'm always operational!",
            ]
        elif "?" in user_message:
            responses = [
                f"That's an interesting question about '{user_message[:50]}...'. Here's a dummy answer: The solution involves multiple factors.",
                "Based on your query, here's a simulated response: Consider checking the documentation.",
                "Dummy AI response: I would recommend exploring different approaches to solve this.",
            ]
        else:
            responses = [
                f"I received your message: '{user_message[:50]}...'. This is a dummy response for development/testing.",
                "This is a simulated AI response. In production, real AI would process this request.",
                f"Dummy AI acknowledges: {user_message[:30]}... Processing complete.",
                "Mock response generated successfully. Replace with real AI provider for production use.",
            ]

        return random.choice(responses)

    def is_available(self) -> bool:
        """Dummy provider is always available"""
        return True
