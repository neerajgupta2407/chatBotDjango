"""Test cases for AnthropicProvider"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from django.test import TestCase, override_settings

from ai_providers.anthropic_provider import AnthropicProvider


class AnthropicProviderTestCase(TestCase):
    """Test cases for AnthropicProvider class"""

    def setUp(self):
        """Set up test instance with mocked Anthropic client"""
        self.api_key = "test-anthropic-key-123"
        with patch("ai_providers.anthropic_provider.Anthropic"):
            self.provider = AnthropicProvider(api_key=self.api_key)

    def test_provider_initialization(self):
        """Should initialize provider with api key"""
        # Assert
        self.assertEqual(self.api_key, self.provider.api_key)
        self.assertIsNotNone(self.provider._client)

    def test_provider_name_property(self):
        """Should return correct provider name"""
        # Act
        name = self.provider.provider_name

        # Assert
        self.assertEqual("claude", name)

    @override_settings(CLAUDE_MODEL="claude-3-opus-20240229")
    def test_default_model_property(self):
        """Should return default model from settings"""
        # Act
        model = self.provider.default_model

        # Assert
        self.assertEqual("claude-3-opus-20240229", model)

    def test_is_available_with_api_key_and_client(self):
        """Should return True when api key and client are set"""
        # Act
        available = self.provider.is_available()

        # Assert
        self.assertTrue(available)

    def test_is_available_without_api_key(self):
        """Should return False when api key is missing"""
        # Arrange
        self.provider.api_key = None

        # Act
        available = self.provider.is_available()

        # Assert
        self.assertFalse(available)

    def test_is_available_without_client(self):
        """Should return False when client is missing"""
        # Arrange
        self.provider._client = None

        # Act
        available = self.provider.is_available()

        # Assert
        self.assertFalse(available)

    @override_settings(
        CLAUDE_MODEL="claude-3-haiku-20240307", CLAUDE_BOT_NAME="Claude AI"
    )
    @patch("ai_providers.anthropic_provider.Anthropic")
    def test_generate_response_success(self, mock_anthropic_class):
        """Should generate response successfully with default settings"""
        # Arrange
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Create mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="This is Claude's response")]
        mock_response.usage = Mock(input_tokens=50, output_tokens=30)

        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Hello Claude"}]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(provider.generate_response(messages))

        # Assert
        self.assertEqual("This is Claude's response", response["content"])
        self.assertEqual("claude", response["provider"])
        self.assertEqual("Claude AI", response["providerName"])
        self.assertEqual("claude-3-haiku-20240307", response["model"])
        self.assertEqual(50, response["usage"]["inputTokens"])
        self.assertEqual(30, response["usage"]["outputTokens"])

        # Verify API was called correctly
        mock_client.messages.create.assert_called_once_with(
            model="claude-3-haiku-20240307", max_tokens=1000, messages=messages
        )

    @override_settings(CLAUDE_MODEL="claude-3-opus-20240229")
    @patch("ai_providers.anthropic_provider.Anthropic")
    def test_generate_response_with_custom_model(self, mock_anthropic_class):
        """Should use custom model when provided in options"""
        # Arrange
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_response.usage = Mock(input_tokens=10, output_tokens=20)

        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]
        options = {"model": "claude-3-5-sonnet-20241022"}

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            provider.generate_response(messages, options)
        )

        # Assert
        self.assertEqual("claude-3-5-sonnet-20241022", response["model"])
        mock_client.messages.create.assert_called_once_with(
            model="claude-3-5-sonnet-20241022", max_tokens=1000, messages=messages
        )

    @patch("ai_providers.anthropic_provider.Anthropic")
    def test_generate_response_with_custom_max_tokens(self, mock_anthropic_class):
        """Should use custom max_tokens when provided"""
        # Arrange
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_response.usage = Mock(input_tokens=10, output_tokens=20)

        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]
        options = {"maxTokens": 2000}

        # Act
        loop = asyncio.get_event_loop()
        loop.run_until_complete(provider.generate_response(messages, options))

        # Assert
        call_args = mock_client.messages.create.call_args
        self.assertEqual(2000, call_args.kwargs["max_tokens"])

    @override_settings(CLAUDE_MODEL="claude-3-haiku-20240307")
    @patch("ai_providers.anthropic_provider.Anthropic")
    def test_generate_response_with_temperature(self, mock_anthropic_class):
        """Should include temperature when provided"""
        # Arrange
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_response.usage = Mock(input_tokens=10, output_tokens=20)

        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]
        options = {"temperature": 0.7}

        # Act
        loop = asyncio.get_event_loop()
        loop.run_until_complete(provider.generate_response(messages, options))

        # Assert
        mock_client.messages.create.assert_called_once_with(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=messages,
            temperature=0.7,
        )

    @override_settings(CLAUDE_MODEL="claude-3-haiku-20240307")
    @patch("ai_providers.anthropic_provider.Anthropic")
    def test_generate_response_without_temperature(self, mock_anthropic_class):
        """Should not include temperature when not provided"""
        # Arrange
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_response.usage = Mock(input_tokens=10, output_tokens=20)

        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]

        # Act
        loop = asyncio.get_event_loop()
        loop.run_until_complete(provider.generate_response(messages))

        # Assert
        call_kwargs = mock_client.messages.create.call_args.kwargs
        self.assertNotIn("temperature", call_kwargs)

    @patch("ai_providers.anthropic_provider.Anthropic")
    def test_generate_response_with_none_options(self, mock_anthropic_class):
        """Should handle None options parameter"""
        # Arrange
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_response.usage = Mock(input_tokens=10, output_tokens=20)

        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(provider.generate_response(messages, None))

        # Assert
        self.assertIsInstance(response, dict)
        self.assertIn("content", response)

    @override_settings(CLAUDE_MODEL="claude-3-haiku-20240307")
    @patch("ai_providers.anthropic_provider.Anthropic")
    def test_generate_response_with_conversation_history(self, mock_anthropic_class):
        """Should handle multiple messages in conversation"""
        # Arrange
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="Response to conversation")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider(api_key="test-key")
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
        ]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(provider.generate_response(messages))

        # Assert
        self.assertEqual("Response to conversation", response["content"])
        # Verify all messages were passed to API
        call_args = mock_client.messages.create.call_args
        self.assertEqual(messages, call_args.kwargs["messages"])

    @patch("ai_providers.anthropic_provider.Anthropic")
    def test_generate_response_api_error(self, mock_anthropic_class):
        """Should raise exception when API call fails"""
        # Arrange
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_client.messages.create.side_effect = Exception("API Error")

        provider = AnthropicProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]

        # Act & Assert
        loop = asyncio.get_event_loop()
        with self.assertRaises(Exception) as context:
            loop.run_until_complete(provider.generate_response(messages))

        self.assertEqual("API Error", str(context.exception))
