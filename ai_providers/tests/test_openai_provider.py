"""Test cases for OpenAIProvider"""

import asyncio
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from ai_providers.openai_provider import OpenAIProvider


class OpenAIProviderTestCase(TestCase):
    """Test cases for OpenAIProvider class"""

    def setUp(self):
        """Set up test instance with mocked OpenAI client"""
        self.api_key = "test-openai-key-123"
        with patch("ai_providers.openai_provider.OpenAI"):
            self.provider = OpenAIProvider(api_key=self.api_key)

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
        self.assertEqual("openai", name)

    @override_settings(OPENAI_MODEL="gpt-4o")
    def test_default_model_property(self):
        """Should return default model from settings"""
        # Act
        model = self.provider.default_model

        # Assert
        self.assertEqual("gpt-4o", model)

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

    @override_settings(OPENAI_MODEL="gpt-4o-mini", OPENAI_BOT_NAME="GPT Assistant")
    @patch("ai_providers.openai_provider.OpenAI")
    def test_generate_response_success(self, mock_openai_class):
        """Should generate response successfully with default settings"""
        # Arrange
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Create mock response
        mock_message = Mock(content="This is GPT's response")
        mock_choice = Mock(message=mock_message)
        mock_usage = Mock(prompt_tokens=50, completion_tokens=30, total_tokens=80)
        mock_response = Mock(choices=[mock_choice], usage=mock_usage)

        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Hello GPT"}]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(provider.generate_response(messages))

        # Assert
        self.assertEqual("This is GPT's response", response["content"])
        self.assertEqual("openai", response["provider"])
        self.assertEqual("GPT Assistant", response["providerName"])
        self.assertEqual("gpt-4o-mini", response["model"])
        self.assertEqual(50, response["usage"]["inputTokens"])
        self.assertEqual(30, response["usage"]["outputTokens"])
        self.assertEqual(80, response["usage"]["totalTokens"])

        # Verify API was called correctly
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4o-mini", max_tokens=1000, messages=messages
        )

    @override_settings(OPENAI_MODEL="gpt-4o")
    @patch("ai_providers.openai_provider.OpenAI")
    def test_generate_response_with_custom_model(self, mock_openai_class):
        """Should use custom model when provided in options"""
        # Arrange
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_message = Mock(content="Response")
        mock_choice = Mock(message=mock_message)
        mock_usage = Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_response = Mock(choices=[mock_choice], usage=mock_usage)

        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]
        options = {"model": "gpt-4-turbo"}

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            provider.generate_response(messages, options)
        )

        # Assert
        self.assertEqual("gpt-4-turbo", response["model"])
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4-turbo", max_tokens=1000, messages=messages
        )

    @override_settings(OPENAI_MODEL="gpt-4o")
    @patch("ai_providers.openai_provider.OpenAI")
    def test_generate_response_with_custom_max_tokens(self, mock_openai_class):
        """Should use custom max_tokens when provided (GPT-4)"""
        # Arrange
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_message = Mock(content="Response")
        mock_choice = Mock(message=mock_message)
        mock_usage = Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_response = Mock(choices=[mock_choice], usage=mock_usage)

        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]
        options = {"maxTokens": 2000}

        # Act
        loop = asyncio.get_event_loop()
        loop.run_until_complete(provider.generate_response(messages, options))

        # Assert
        call_args = mock_client.chat.completions.create.call_args
        self.assertEqual(2000, call_args.kwargs["max_tokens"])

    @override_settings(OPENAI_MODEL="gpt-4o")
    @patch("ai_providers.openai_provider.OpenAI")
    def test_generate_response_with_temperature(self, mock_openai_class):
        """Should include temperature when provided"""
        # Arrange
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_message = Mock(content="Response")
        mock_choice = Mock(message=mock_message)
        mock_usage = Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_response = Mock(choices=[mock_choice], usage=mock_usage)

        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]
        options = {"temperature": 0.8}

        # Act
        loop = asyncio.get_event_loop()
        loop.run_until_complete(provider.generate_response(messages, options))

        # Assert
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4o", max_tokens=1000, messages=messages, temperature=0.8
        )

    @override_settings(OPENAI_MODEL="gpt-4o")
    @patch("ai_providers.openai_provider.OpenAI")
    def test_generate_response_without_temperature(self, mock_openai_class):
        """Should not include temperature when not provided"""
        # Arrange
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_message = Mock(content="Response")
        mock_choice = Mock(message=mock_message)
        mock_usage = Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_response = Mock(choices=[mock_choice], usage=mock_usage)

        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]

        # Act
        loop = asyncio.get_event_loop()
        loop.run_until_complete(provider.generate_response(messages))

        # Assert
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        self.assertNotIn("temperature", call_kwargs)

    @patch("ai_providers.openai_provider.OpenAI")
    def test_generate_response_with_none_options(self, mock_openai_class):
        """Should handle None options parameter"""
        # Arrange
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_message = Mock(content="Response")
        mock_choice = Mock(message=mock_message)
        mock_usage = Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_response = Mock(choices=[mock_choice], usage=mock_usage)

        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(provider.generate_response(messages, None))

        # Assert
        self.assertIsInstance(response, dict)
        self.assertIn("content", response)

    @override_settings(OPENAI_MODEL="gpt-4o")
    @patch("ai_providers.openai_provider.OpenAI")
    def test_generate_response_with_conversation_history(self, mock_openai_class):
        """Should handle multiple messages in conversation"""
        # Arrange
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_message = Mock(content="Response to conversation")
        mock_choice = Mock(message=mock_message)
        mock_usage = Mock(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        mock_response = Mock(choices=[mock_choice], usage=mock_usage)

        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="test-key")
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
        call_args = mock_client.chat.completions.create.call_args
        self.assertEqual(messages, call_args.kwargs["messages"])

    @patch("ai_providers.openai_provider.OpenAI")
    def test_generate_response_api_error(self, mock_openai_class):
        """Should raise exception when API call fails"""
        # Arrange
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_client.chat.completions.create.side_effect = Exception("API Error")

        provider = OpenAIProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]

        # Act & Assert
        loop = asyncio.get_event_loop()
        with self.assertRaises(Exception) as context:
            loop.run_until_complete(provider.generate_response(messages))

        self.assertEqual("API Error", str(context.exception))

    @override_settings(OPENAI_MODEL="gpt-4o")
    @patch("ai_providers.openai_provider.OpenAI")
    def test_generate_response_includes_total_tokens(self, mock_openai_class):
        """Should include totalTokens in usage statistics"""
        # Arrange
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_message = Mock(content="Response")
        mock_choice = Mock(message=mock_message)
        mock_usage = Mock(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        mock_response = Mock(choices=[mock_choice], usage=mock_usage)

        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Test"}]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(provider.generate_response(messages))

        # Assert
        self.assertIn("totalTokens", response["usage"])
        self.assertEqual(150, response["usage"]["totalTokens"])
        self.assertEqual(100, response["usage"]["inputTokens"])
        self.assertEqual(50, response["usage"]["outputTokens"])
