"""Test cases for AIProviderFactory"""

import asyncio
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from ai_providers.factory import AIProviderFactory


class AIProviderFactoryTestCase(TestCase):
    """Test cases for AIProviderFactory singleton"""

    def setUp(self):
        """Reset factory singleton for each test"""
        # Clear the singleton instance to allow fresh initialization
        AIProviderFactory._instance = None
        if hasattr(AIProviderFactory, "_providers"):
            AIProviderFactory._providers.clear()

    def tearDown(self):
        """Clean up after each test"""
        # Reset singleton instance and providers
        AIProviderFactory._instance = None
        if hasattr(AIProviderFactory, "_providers"):
            AIProviderFactory._providers.clear()

    @override_settings(
        ANTHROPIC_API_KEY="test-anthropic-key",
        OPENAI_API_KEY=None,
        ENABLE_DUMMY_PROVIDER=False,
    )
    @patch("ai_providers.factory.AnthropicProvider")
    def test_factory_singleton_pattern(self, mock_anthropic):
        """Should implement singleton pattern correctly"""
        # Act
        factory1 = AIProviderFactory()
        factory2 = AIProviderFactory()

        # Assert
        self.assertIs(factory1, factory2)

    @override_settings(
        ANTHROPIC_API_KEY="test-anthropic-key",
        OPENAI_API_KEY=None,
        ENABLE_DUMMY_PROVIDER=False,
    )
    @patch("ai_providers.factory.AnthropicProvider")
    def test_initialize_providers_with_anthropic_only(self, mock_anthropic):
        """Should initialize only Claude when only Anthropic key is set"""
        # Act
        factory = AIProviderFactory()

        # Assert
        self.assertIn("claude", factory._providers)
        self.assertNotIn("openai", factory._providers)
        self.assertNotIn("dummy", factory._providers)
        mock_anthropic.assert_called_once_with(api_key="test-anthropic-key")

    @override_settings(
        ANTHROPIC_API_KEY=None,
        OPENAI_API_KEY="test-openai-key",
        ENABLE_DUMMY_PROVIDER=False,
    )
    @patch("ai_providers.factory.OpenAIProvider")
    def test_initialize_providers_with_openai_only(self, mock_openai):
        """Should initialize only OpenAI when only OpenAI key is set"""
        # Act
        factory = AIProviderFactory()

        # Assert
        self.assertIn("openai", factory._providers)
        self.assertNotIn("claude", factory._providers)
        self.assertNotIn("dummy", factory._providers)
        mock_openai.assert_called_once_with(api_key="test-openai-key")

    @override_settings(
        ANTHROPIC_API_KEY="test-anthropic-key",
        OPENAI_API_KEY="test-openai-key",
        ENABLE_DUMMY_PROVIDER=False,
    )
    @patch("ai_providers.factory.OpenAIProvider")
    @patch("ai_providers.factory.AnthropicProvider")
    def test_initialize_providers_with_both_keys(self, mock_anthropic, mock_openai):
        """Should initialize both providers when both keys are set"""
        # Act
        factory = AIProviderFactory()

        # Assert
        self.assertIn("claude", factory._providers)
        self.assertIn("openai", factory._providers)
        self.assertNotIn("dummy", factory._providers)
        mock_anthropic.assert_called_once_with(api_key="test-anthropic-key")
        mock_openai.assert_called_once_with(api_key="test-openai-key")

    @override_settings(
        ANTHROPIC_API_KEY=None,
        OPENAI_API_KEY=None,
        ENABLE_DUMMY_PROVIDER=True,
    )
    @patch("ai_providers.factory.DummyProvider")
    def test_initialize_providers_with_dummy_enabled(self, mock_dummy):
        """Should initialize dummy provider when enabled"""
        # Act
        factory = AIProviderFactory()

        # Assert
        self.assertIn("dummy", factory._providers)
        self.assertNotIn("claude", factory._providers)
        self.assertNotIn("openai", factory._providers)
        mock_dummy.assert_called_once()

    @override_settings(
        ANTHROPIC_API_KEY=None,
        OPENAI_API_KEY=None,
        ENABLE_DUMMY_PROVIDER=False,
    )
    def test_initialize_providers_with_no_keys(self):
        """Should have no providers when no keys are set"""
        # Act
        factory = AIProviderFactory()

        # Assert
        self.assertEqual(0, len(factory._providers))

    @override_settings(
        ANTHROPIC_API_KEY="test-key",
        AI_PROVIDER="claude",
        ENABLE_DUMMY_PROVIDER=False,
    )
    @patch("ai_providers.factory.AnthropicProvider")
    def test_get_provider_with_default_setting(self, mock_anthropic):
        """Should return default provider from settings"""
        # Arrange
        mock_provider = Mock()
        mock_anthropic.return_value = mock_provider
        factory = AIProviderFactory()

        # Act
        provider = factory.get_provider()

        # Assert
        self.assertEqual(mock_provider, provider)

    @override_settings(
        ANTHROPIC_API_KEY="test-anthropic-key",
        OPENAI_API_KEY="test-openai-key",
        AI_PROVIDER="claude",
        ENABLE_DUMMY_PROVIDER=False,
    )
    @patch("ai_providers.factory.OpenAIProvider")
    @patch("ai_providers.factory.AnthropicProvider")
    def test_get_provider_with_specific_name(self, mock_anthropic, mock_openai):
        """Should return specific provider when name is provided"""
        # Arrange
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        factory = AIProviderFactory()

        # Act
        provider = factory.get_provider("openai")

        # Assert
        self.assertEqual(mock_openai_instance, provider)

    @override_settings(
        ANTHROPIC_API_KEY="test-key",
        OPENAI_API_KEY=None,
        ENABLE_DUMMY_PROVIDER=False,
    )
    @patch("ai_providers.factory.OpenAIProvider")
    @patch("ai_providers.factory.AnthropicProvider")
    def test_get_provider_unavailable(self, mock_anthropic, mock_openai):
        """Should raise ValueError when provider is not available"""
        # Arrange
        # Reset factory to ensure clean state
        AIProviderFactory._instance = None
        AIProviderFactory._providers.clear()
        factory = AIProviderFactory()

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            factory.get_provider("openai")

        self.assertIn("not available", str(context.exception))
        self.assertIn("openai", str(context.exception))

    @override_settings(
        ANTHROPIC_API_KEY="test-anthropic-key",
        OPENAI_API_KEY="test-openai-key",
        ENABLE_DUMMY_PROVIDER=False,
    )
    @patch("ai_providers.factory.OpenAIProvider")
    @patch("ai_providers.factory.AnthropicProvider")
    def test_get_available_providers(self, mock_anthropic, mock_openai):
        """Should return list of available providers"""
        # Arrange
        factory = AIProviderFactory()

        # Act
        providers = factory.get_available_providers()

        # Assert
        self.assertIsInstance(providers, list)
        self.assertIn("claude", providers)
        self.assertIn("openai", providers)
        self.assertEqual(2, len(providers))

    @override_settings(
        ANTHROPIC_API_KEY="test-key",
        ENABLE_DUMMY_PROVIDER=False,
    )
    @patch("ai_providers.factory.AnthropicProvider")
    def test_is_provider_available_true(self, mock_anthropic):
        """Should return True for available provider"""
        # Arrange
        factory = AIProviderFactory()

        # Act
        is_available = factory.is_provider_available("claude")

        # Assert
        self.assertTrue(is_available)

    @override_settings(
        ANTHROPIC_API_KEY="test-key",
        OPENAI_API_KEY=None,
        ENABLE_DUMMY_PROVIDER=False,
    )
    @patch("ai_providers.factory.OpenAIProvider")
    @patch("ai_providers.factory.AnthropicProvider")
    def test_is_provider_available_false(self, mock_anthropic, mock_openai):
        """Should return False for unavailable provider"""
        # Arrange
        # Reset factory to ensure clean state
        AIProviderFactory._instance = None
        AIProviderFactory._providers.clear()
        factory = AIProviderFactory()

        # Act
        is_available = factory.is_provider_available("openai")

        # Assert
        self.assertFalse(is_available)

    @override_settings(
        ANTHROPIC_API_KEY="test-key",
        AI_PROVIDER="claude",
        CLAUDE_MODEL="claude-3-haiku-20240307",
        ENABLE_DUMMY_PROVIDER=False,
    )
    @patch("ai_providers.factory.AnthropicProvider")
    def test_generate_response_with_default_provider(self, mock_anthropic):
        """Should use default provider when none specified"""
        # Arrange
        mock_provider = Mock()
        mock_response = {
            "content": "Test response",
            "provider": "claude",
            "model": "claude-3-haiku-20240307",
        }
        mock_provider.generate_response = Mock(return_value=mock_response)
        mock_anthropic.return_value = mock_provider

        factory = AIProviderFactory()
        messages = [{"role": "user", "content": "Test"}]

        # Act
        loop = asyncio.get_event_loop()

        # Mock the async call
        async def mock_generate(*args, **kwargs):
            return mock_response

        mock_provider.generate_response = mock_generate
        response = loop.run_until_complete(factory.generate_response(None, messages))

        # Assert
        self.assertEqual("Test response", response["content"])

    @override_settings(
        ANTHROPIC_API_KEY="test-anthropic-key",
        OPENAI_API_KEY="test-openai-key",
        AI_PROVIDER="claude",
        ENABLE_DUMMY_PROVIDER=False,
    )
    @patch("ai_providers.factory.OpenAIProvider")
    @patch("ai_providers.factory.AnthropicProvider")
    def test_generate_response_with_specific_provider(
        self, mock_anthropic, mock_openai
    ):
        """Should use specific provider when name is provided"""
        # Arrange
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance

        mock_response = {
            "content": "OpenAI response",
            "provider": "openai",
            "model": "gpt-4o",
        }

        async def mock_generate(*args, **kwargs):
            return mock_response

        mock_openai_instance.generate_response = mock_generate

        factory = AIProviderFactory()
        messages = [{"role": "user", "content": "Test"}]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            factory.generate_response("openai", messages)
        )

        # Assert
        self.assertEqual("OpenAI response", response["content"])
        self.assertEqual("openai", response["provider"])

    @override_settings(
        ANTHROPIC_API_KEY="test-key",
        AI_PROVIDER="claude",
        ENABLE_DUMMY_PROVIDER=False,
    )
    @patch("ai_providers.factory.AnthropicProvider")
    def test_generate_response_with_options(self, mock_anthropic):
        """Should pass options to provider"""
        # Arrange
        mock_provider = Mock()
        mock_anthropic.return_value = mock_provider

        mock_response = {"content": "Response", "provider": "claude"}

        async def mock_generate(messages, options=None):
            return {**mock_response, "options_received": options}

        mock_provider.generate_response = mock_generate

        factory = AIProviderFactory()
        messages = [{"role": "user", "content": "Test"}]
        options = {"temperature": 0.7, "maxTokens": 2000}

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            factory.generate_response("claude", messages, options)
        )

        # Assert
        self.assertEqual(options, response["options_received"])

    @override_settings(
        ANTHROPIC_API_KEY="test-key",
        AI_PROVIDER="claude",
        ENABLE_DUMMY_PROVIDER=False,
    )
    @patch("ai_providers.factory.AnthropicProvider")
    def test_generate_response_with_none_options(self, mock_anthropic):
        """Should handle None options parameter"""
        # Arrange
        mock_provider = Mock()
        mock_anthropic.return_value = mock_provider

        mock_response = {"content": "Response", "provider": "claude"}

        async def mock_generate(messages, options=None):
            return mock_response

        mock_provider.generate_response = mock_generate

        factory = AIProviderFactory()
        messages = [{"role": "user", "content": "Test"}]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            factory.generate_response("claude", messages, None)
        )

        # Assert
        self.assertEqual("Response", response["content"])

    @override_settings(
        ANTHROPIC_API_KEY="test-key",
        OPENAI_API_KEY=None,
        ENABLE_DUMMY_PROVIDER=False,
    )
    @patch("ai_providers.factory.OpenAIProvider")
    @patch("ai_providers.factory.AnthropicProvider")
    def test_generate_response_with_unavailable_provider(
        self, mock_anthropic, mock_openai
    ):
        """Should raise ValueError when provider is not available"""
        # Arrange
        # Reset factory to ensure clean state
        AIProviderFactory._instance = None
        AIProviderFactory._providers.clear()
        factory = AIProviderFactory()
        messages = [{"role": "user", "content": "Test"}]

        # Act & Assert
        loop = asyncio.get_event_loop()
        with self.assertRaises(ValueError) as context:
            loop.run_until_complete(factory.generate_response("openai", messages))

        self.assertIn("not available", str(context.exception))
