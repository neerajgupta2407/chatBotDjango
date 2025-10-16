"""Tests for system_prompt integration in chat functionality"""

from django.test import TestCase
from model_bakery import baker

from chat.services import ChatService


class SystemPromptIntegrationTestCase(TestCase):
    """Test that custom system prompts are properly integrated"""

    def test_build_context_with_custom_system_prompt(self):
        """Should use custom system_prompt when provided"""
        custom_prompt = "You are a specialized real estate assistant."
        user_message = "Tell me about this property"
        session_config = {}
        conversation_history = []

        context = ChatService.build_context_prompt(
            user_message=user_message,
            session_config=session_config,
            conversation_history=conversation_history,
            file_data=None,
            system_prompt=custom_prompt,
        )

        # Custom prompt should be at the start
        self.assertIn(custom_prompt, context)
        self.assertIn(user_message, context)

    def test_build_context_without_system_prompt(self):
        """Should use default prompt when system_prompt is None"""
        user_message = "Hello"
        session_config = {}
        conversation_history = []

        context = ChatService.build_context_prompt(
            user_message=user_message,
            session_config=session_config,
            conversation_history=conversation_history,
            file_data=None,
            system_prompt=None,
        )

        # Default prompt should be used
        self.assertIn("helpful assistant", context)
        self.assertIn(user_message, context)

    def test_build_context_with_empty_system_prompt(self):
        """Should use default prompt when system_prompt is empty string"""
        user_message = "Hello"
        session_config = {}
        conversation_history = []

        context = ChatService.build_context_prompt(
            user_message=user_message,
            session_config=session_config,
            conversation_history=conversation_history,
            file_data=None,
            system_prompt="",
        )

        # Default prompt should be used (empty string is falsy)
        self.assertIn("helpful assistant", context)
        self.assertIn(user_message, context)

    def test_custom_system_prompt_with_page_context(self):
        """Should include both custom system prompt and page information"""
        custom_prompt = "You are a real estate expert."
        user_message = "What's the price?"
        session_config = {
            "pageContext": {
                "url": "https://example.com/property/123",
                "title": "Luxury Villa",
            }
        }
        conversation_history = []

        context = ChatService.build_context_prompt(
            user_message=user_message,
            session_config=session_config,
            conversation_history=conversation_history,
            file_data=None,
            system_prompt=custom_prompt,
        )

        # Should include custom prompt, page info, and user message
        self.assertIn(custom_prompt, context)
        self.assertIn("Luxury Villa", context)
        self.assertIn("https://example.com/property/123", context)
        self.assertIn(user_message, context)
