"""Test cases for DummyProvider"""

import asyncio

from django.test import TestCase, override_settings

from ai_providers.dummy_provider import DummyProvider


class DummyProviderTestCase(TestCase):
    """Test cases for DummyProvider class"""

    def setUp(self):
        """Set up test instance"""
        self.provider = DummyProvider()

    def test_provider_initialization(self):
        """Should initialize dummy provider with default api key"""
        # Arrange & Act - done in setUp

        # Assert
        self.assertEqual("dummy-key", self.provider.api_key)
        self.assertTrue(self.provider._client)

    def test_provider_initialization_with_custom_key(self):
        """Should initialize dummy provider with custom api key"""
        # Arrange & Act
        custom_provider = DummyProvider(api_key="custom-key-123")

        # Assert
        self.assertEqual("custom-key-123", custom_provider.api_key)

    def test_provider_name_property(self):
        """Should return correct provider name"""
        # Act
        name = self.provider.provider_name

        # Assert
        self.assertEqual("dummy", name)

    @override_settings(DUMMY_MODEL="test-model-1.0")
    def test_default_model_property(self):
        """Should return default model from settings"""
        # Act
        model = self.provider.default_model

        # Assert
        self.assertEqual("test-model-1.0", model)

    def test_is_available(self):
        """Should always return True for dummy provider"""
        # Act
        available = self.provider.is_available()

        # Assert
        self.assertTrue(available)

    def test_generate_response_with_greeting(self):
        """Should generate contextual greeting response"""
        # Arrange
        messages = [{"role": "user", "content": "Hello there!"}]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.provider.generate_response(messages))

        # Assert
        self.assertIn("content", response)
        self.assertIn("provider", response)
        self.assertIn("model", response)
        self.assertIn("usage", response)
        self.assertEqual("dummy", response["provider"])
        # Greeting responses contain greeting-related words
        content_lower = response["content"].lower()
        self.assertTrue(
            "hello" in content_lower
            or "hi" in content_lower
            or "greet" in content_lower
        )

    def test_generate_response_with_question(self):
        """Should generate contextual question response"""
        # Arrange
        messages = [{"role": "user", "content": "How does this work?"}]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.provider.generate_response(messages))

        # Assert
        self.assertIn("content", response)
        self.assertEqual("dummy", response["provider"])
        self.assertIsInstance(response["content"], str)
        self.assertGreater(len(response["content"]), 0)

    def test_generate_response_with_how_are_you(self):
        """Should generate contextual response to 'how are you'"""
        # Arrange
        messages = [{"role": "user", "content": "How are you?"}]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.provider.generate_response(messages))

        # Assert
        self.assertIn("dummy", response["content"].lower())

    def test_generate_response_with_generic_message(self):
        """Should generate generic response for non-special messages"""
        # Arrange
        messages = [{"role": "user", "content": "This is a test message"}]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.provider.generate_response(messages))

        # Assert
        self.assertIsInstance(response["content"], str)
        self.assertGreater(len(response["content"]), 0)

    def test_generate_response_with_custom_model(self):
        """Should use custom model when provided in options"""
        # Arrange
        messages = [{"role": "user", "content": "Test"}]
        options = {"model": "custom-model-2.0"}

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self.provider.generate_response(messages, options)
        )

        # Assert
        self.assertEqual("custom-model-2.0", response["model"])

    @override_settings(DUMMY_MODEL="default-model-1.0")
    def test_generate_response_uses_default_model(self):
        """Should use default model when not specified in options"""
        # Arrange
        messages = [{"role": "user", "content": "Test"}]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.provider.generate_response(messages))

        # Assert
        self.assertEqual("default-model-1.0", response["model"])

    def test_generate_response_calculates_token_usage(self):
        """Should calculate token usage based on message content"""
        # Arrange
        messages = [
            {"role": "user", "content": "Hello this is a test message"},
            {"role": "assistant", "content": "Response here"},
            {"role": "user", "content": "Another message"},
        ]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.provider.generate_response(messages))

        # Assert
        self.assertIn("usage", response)
        self.assertIn("inputTokens", response["usage"])
        self.assertIn("outputTokens", response["usage"])
        self.assertIn("totalTokens", response["usage"])
        self.assertGreater(response["usage"]["inputTokens"], 0)
        self.assertGreater(response["usage"]["outputTokens"], 0)
        self.assertEqual(
            response["usage"]["inputTokens"] + response["usage"]["outputTokens"],
            response["usage"]["totalTokens"],
        )

    def test_generate_response_with_conversation_history(self):
        """Should handle multiple messages in conversation"""
        # Arrange
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How can you help?"},
        ]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.provider.generate_response(messages))

        # Assert
        self.assertIsInstance(response["content"], str)
        self.assertEqual("dummy", response["provider"])

    def test_generate_response_with_empty_options(self):
        """Should handle None options parameter"""
        # Arrange
        messages = [{"role": "user", "content": "Test"}]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self.provider.generate_response(messages, None)
        )

        # Assert
        self.assertIsInstance(response, dict)
        self.assertIn("content", response)

    @override_settings(DUMMY_BOT_NAME="Test Dummy Bot")
    def test_generate_response_includes_provider_name(self):
        """Should include provider name from settings"""
        # Arrange
        messages = [{"role": "user", "content": "Test"}]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.provider.generate_response(messages))

        # Assert
        self.assertEqual("Test Dummy Bot", response["providerName"])

    def test_generate_response_greeting_hello(self):
        """Should recognize Hello greeting"""
        # Arrange
        messages = [{"role": "user", "content": "Hello"}]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.provider.generate_response(messages))

        # Assert
        # Greeting responses contain greeting-related words
        content_lower = response["content"].lower()
        self.assertTrue(
            "hello" in content_lower
            or "hi" in content_lower
            or "greet" in content_lower
        )

    def test_generate_response_greeting_hi(self):
        """Should recognize Hi greeting"""
        # Arrange
        messages = [{"role": "user", "content": "Hi there"}]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.provider.generate_response(messages))

        # Assert
        # Greeting responses contain greeting-related words
        content_lower = response["content"].lower()
        self.assertTrue(
            "hi" in content_lower
            or "hello" in content_lower
            or "greet" in content_lower
        )

    def test_generate_response_greeting_uppercase(self):
        """Should recognize uppercase HELLO greeting"""
        # Arrange
        messages = [{"role": "user", "content": "HELLO!"}]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.provider.generate_response(messages))

        # Assert
        # Greeting responses contain greeting-related words
        content_lower = response["content"].lower()
        self.assertTrue(
            "hello" in content_lower
            or "hi" in content_lower
            or "greet" in content_lower
        )

    def test_generate_response_extracts_last_user_message(self):
        """Should respond based on the last user message"""
        # Arrange
        messages = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "First response"},
            {"role": "user", "content": "Hello!"},  # Last user message
        ]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.provider.generate_response(messages))

        # Assert
        # Should respond to "Hello!" not "First message"
        content_lower = response["content"].lower()
        self.assertTrue(
            "hello" in content_lower
            or "hi" in content_lower
            or "greet" in content_lower
        )

    def test_generate_response_handles_no_user_messages(self):
        """Should handle messages with no user role"""
        # Arrange
        messages = [{"role": "system", "content": "System message"}]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.provider.generate_response(messages))

        # Assert
        self.assertIsInstance(response["content"], str)
        self.assertGreater(len(response["content"]), 0)

    def test_generate_response_long_message_truncation(self):
        """Should handle long messages gracefully"""
        # Arrange
        long_message = "a" * 1000  # Very long message
        messages = [{"role": "user", "content": long_message}]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.provider.generate_response(messages))

        # Assert
        self.assertIsInstance(response["content"], str)
        # Response should still be generated
        self.assertGreater(len(response["content"]), 0)
