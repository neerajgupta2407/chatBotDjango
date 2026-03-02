"""Test cases for DataForSEO integration with AI providers and chat views"""

import asyncio
import json
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from model_bakery import baker

from ai_providers.anthropic_provider import AnthropicProvider
from ai_providers.openai_provider import OpenAIProvider
from chat.models import Message, Session
from chat.services import ChatService
from chat.views.messages import _resolve_dataforseo_modules


class AnthropicToolCallingTestCase(TestCase):
    """Test cases for Anthropic provider tool calling support"""

    def setUp(self):
        with patch("ai_providers.anthropic_provider.Anthropic"):
            self.provider = AnthropicProvider(api_key="test-key")

    def test_convert_messages_extracts_system(self):
        """Should extract system message into separate parameter"""
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
        ]

        system_prompt, converted = self.provider._convert_messages(messages)

        self.assertEqual("You are helpful.", system_prompt)
        self.assertEqual(1, len(converted))
        self.assertEqual("user", converted[0]["role"])

    def test_convert_messages_assistant_with_tool_calls(self):
        """Should convert assistant tool_calls to Anthropic content blocks"""
        messages = [
            {"role": "user", "content": "Search for python"},
            {
                "role": "assistant",
                "content": "Let me search.",
                "tool_calls": [
                    {
                        "id": "toolu_123",
                        "name": "serp_google_organic_live",
                        "input": {"keyword": "python"},
                    }
                ],
            },
        ]

        _, converted = self.provider._convert_messages(messages)

        self.assertEqual(2, len(converted))
        assistant_msg = converted[1]
        self.assertEqual("assistant", assistant_msg["role"])
        self.assertIsInstance(assistant_msg["content"], list)
        self.assertEqual("text", assistant_msg["content"][0]["type"])
        self.assertEqual("Let me search.", assistant_msg["content"][0]["text"])
        self.assertEqual("tool_use", assistant_msg["content"][1]["type"])
        self.assertEqual("toolu_123", assistant_msg["content"][1]["id"])
        self.assertEqual(
            "serp_google_organic_live", assistant_msg["content"][1]["name"]
        )

    def test_convert_messages_tool_result(self):
        """Should convert tool results to user message with tool_result blocks"""
        messages = [
            {
                "role": "tool",
                "tool_call_id": "toolu_123",
                "name": "serp_google_organic_live",
                "content": '{"keyword": "python", "organic_results": []}',
            }
        ]

        _, converted = self.provider._convert_messages(messages)

        self.assertEqual(1, len(converted))
        self.assertEqual("user", converted[0]["role"])
        self.assertIsInstance(converted[0]["content"], list)
        self.assertEqual("tool_result", converted[0]["content"][0]["type"])
        self.assertEqual("toolu_123", converted[0]["content"][0]["tool_use_id"])

    def test_convert_messages_groups_consecutive_tool_results(self):
        """Should group consecutive tool results into a single user message"""
        messages = [
            {
                "role": "tool",
                "tool_call_id": "toolu_1",
                "name": "tool_a",
                "content": "result_a",
            },
            {
                "role": "tool",
                "tool_call_id": "toolu_2",
                "name": "tool_b",
                "content": "result_b",
            },
        ]

        _, converted = self.provider._convert_messages(messages)

        self.assertEqual(1, len(converted))
        self.assertEqual("user", converted[0]["role"])
        self.assertEqual(2, len(converted[0]["content"]))

    @override_settings(CLAUDE_MODEL="claude-3-haiku-20240307", CLAUDE_BOT_NAME="Claude")
    @patch("ai_providers.anthropic_provider.Anthropic")
    def test_generate_response_with_tool_use(self, mock_anthropic_class):
        """Should return tool_calls when AI requests tool use"""
        # Arrange
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        text_block = Mock()
        text_block.type = "text"
        text_block.text = "I'll search for that."

        tool_block = Mock()
        tool_block.type = "tool_use"
        tool_block.id = "toolu_abc123"
        tool_block.name = "serp_google_organic_live"
        tool_block.input = {"keyword": "python tutorial"}

        mock_response = Mock()
        mock_response.content = [text_block, tool_block]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Search for python tutorial"}]
        tools = [
            {
                "name": "serp_google_organic_live",
                "description": "Search Google",
                "input_schema": {"type": "object", "properties": {}, "required": []},
            }
        ]

        # Act
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            provider.generate_response(messages, {}, tools=tools)
        )

        # Assert
        self.assertEqual("I'll search for that.", response["content"])
        self.assertIn("tool_calls", response)
        self.assertEqual(1, len(response["tool_calls"]))
        self.assertEqual("toolu_abc123", response["tool_calls"][0]["id"])
        self.assertEqual("serp_google_organic_live", response["tool_calls"][0]["name"])
        self.assertEqual(
            {"keyword": "python tutorial"}, response["tool_calls"][0]["input"]
        )

    @override_settings(CLAUDE_MODEL="claude-3-haiku-20240307", CLAUDE_BOT_NAME="Claude")
    @patch("ai_providers.anthropic_provider.Anthropic")
    def test_generate_response_passes_tools_to_api(self, mock_anthropic_class):
        """Should pass tools parameter to Anthropic API"""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_response.usage = Mock(input_tokens=10, output_tokens=5)

        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Hello"}]
        tools = [{"name": "test_tool", "description": "A test", "input_schema": {}}]

        loop = asyncio.get_event_loop()
        loop.run_until_complete(provider.generate_response(messages, {}, tools=tools))

        call_kwargs = mock_client.messages.create.call_args.kwargs
        self.assertEqual(tools, call_kwargs["tools"])

    @override_settings(CLAUDE_MODEL="claude-3-haiku-20240307", CLAUDE_BOT_NAME="Claude")
    @patch("ai_providers.anthropic_provider.Anthropic")
    def test_generate_response_without_tools_backward_compatible(
        self, mock_anthropic_class
    ):
        """Should work normally when no tools are provided"""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="Normal response")]
        mock_response.usage = Mock(input_tokens=10, output_tokens=5)

        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Hello"}]

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(provider.generate_response(messages))

        self.assertEqual("Normal response", response["content"])
        self.assertNotIn("tool_calls", response)


class OpenAIToolCallingTestCase(TestCase):
    """Test cases for OpenAI provider tool calling support"""

    def setUp(self):
        with patch("ai_providers.openai_provider.OpenAI"):
            self.provider = OpenAIProvider(api_key="test-key")

    def test_convert_tools_format(self):
        """Should convert our tool format to OpenAI function format"""
        tools = [
            {
                "name": "test_tool",
                "description": "A test tool",
                "input_schema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            }
        ]

        converted = self.provider._convert_tools(tools)

        self.assertEqual(1, len(converted))
        self.assertEqual("function", converted[0]["type"])
        self.assertEqual("test_tool", converted[0]["function"]["name"])
        self.assertEqual("A test tool", converted[0]["function"]["description"])
        self.assertEqual(
            tools[0]["input_schema"], converted[0]["function"]["parameters"]
        )

    def test_convert_messages_assistant_tool_calls(self):
        """Should convert assistant tool_calls to OpenAI format"""
        messages = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "name": "serp_google_organic_live",
                        "input": {"keyword": "python"},
                    }
                ],
            }
        ]

        converted = self.provider._convert_messages(messages)

        self.assertEqual(1, len(converted))
        msg = converted[0]
        self.assertEqual("assistant", msg["role"])
        self.assertEqual(1, len(msg["tool_calls"]))
        self.assertEqual("call_123", msg["tool_calls"][0]["id"])
        self.assertEqual("function", msg["tool_calls"][0]["type"])
        self.assertEqual(
            "serp_google_organic_live", msg["tool_calls"][0]["function"]["name"]
        )
        self.assertEqual(
            '{"keyword": "python"}', msg["tool_calls"][0]["function"]["arguments"]
        )

    def test_convert_messages_tool_result(self):
        """Should convert tool result to OpenAI format"""
        messages = [
            {
                "role": "tool",
                "tool_call_id": "call_123",
                "name": "serp_google_organic_live",
                "content": '{"results": []}',
            }
        ]

        converted = self.provider._convert_messages(messages)

        self.assertEqual(1, len(converted))
        self.assertEqual("tool", converted[0]["role"])
        self.assertEqual("call_123", converted[0]["tool_call_id"])

    @override_settings(OPENAI_MODEL="gpt-4o", OPENAI_BOT_NAME="GPT")
    @patch("ai_providers.openai_provider.OpenAI")
    def test_generate_response_with_tool_calls(self, mock_openai_class):
        """Should return tool_calls when AI requests tool use"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_tool_call = Mock()
        mock_tool_call.id = "call_abc123"
        mock_tool_call.function.name = "serp_google_organic_live"
        mock_tool_call.function.arguments = '{"keyword": "python"}'

        mock_message = Mock()
        mock_message.content = None
        mock_message.tool_calls = [mock_tool_call]

        mock_response = Mock()
        mock_response.choices = [Mock(message=mock_message)]
        mock_response.usage = Mock(
            prompt_tokens=50, completion_tokens=20, total_tokens=70
        )

        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="test-key")
        messages = [{"role": "user", "content": "Search for python"}]
        tools = [
            {
                "name": "serp_google_organic_live",
                "description": "Search Google",
                "input_schema": {"type": "object", "properties": {}, "required": []},
            }
        ]

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            provider.generate_response(messages, {}, tools=tools)
        )

        self.assertIn("tool_calls", response)
        self.assertEqual(1, len(response["tool_calls"]))
        self.assertEqual("call_abc123", response["tool_calls"][0]["id"])
        self.assertEqual("serp_google_organic_live", response["tool_calls"][0]["name"])
        self.assertEqual({"keyword": "python"}, response["tool_calls"][0]["input"])

    @override_settings(OPENAI_MODEL="gpt-4o", OPENAI_BOT_NAME="GPT")
    @patch("ai_providers.openai_provider.OpenAI")
    def test_generate_response_passes_converted_tools(self, mock_openai_class):
        """Should convert and pass tools to OpenAI API"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_message = Mock(content="OK", tool_calls=None)
        mock_response = Mock(
            choices=[Mock(message=mock_message)],
            usage=Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )
        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="test-key")
        tools = [
            {
                "name": "test",
                "description": "Test tool",
                "input_schema": {"type": "object", "properties": {}, "required": []},
            }
        ]

        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            provider.generate_response(
                [{"role": "user", "content": "Hi"}], {}, tools=tools
            )
        )

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        self.assertIn("tools", call_kwargs)
        self.assertEqual("function", call_kwargs["tools"][0]["type"])
        self.assertEqual("test", call_kwargs["tools"][0]["function"]["name"])


class ResolveDataForSEOModulesTestCase(TestCase):
    """Test cases for _resolve_dataforseo_modules"""

    def test_session_config_takes_priority(self):
        """Should use session config when set"""
        session = Mock()
        session.config = {"dataforseo_modules": ["SERP"]}
        client = Mock()
        client.config = {"dataforseo_modules": ["BACKLINKS"]}

        result = _resolve_dataforseo_modules(session, client)

        self.assertEqual(["SERP"], result)

    def test_client_config_second_priority(self):
        """Should use client config when session has none"""
        session = Mock()
        session.config = {}
        client = Mock()
        client.config = {"dataforseo_modules": ["BACKLINKS"]}

        result = _resolve_dataforseo_modules(session, client)

        self.assertEqual(["BACKLINKS"], result)

    @override_settings(DATAFORSEO_ENABLED_MODULES="SERP,KEYWORDS_DATA")
    def test_global_setting_fallback(self):
        """Should use global setting when neither session nor client config set"""
        session = Mock()
        session.config = {}
        client = Mock()
        client.config = {}

        result = _resolve_dataforseo_modules(session, client)

        self.assertEqual(["SERP", "KEYWORDS_DATA"], result)

    @override_settings(DATAFORSEO_ENABLED_MODULES="")
    def test_returns_empty_when_nothing_configured(self):
        """Should return empty list when nothing is configured"""
        session = Mock()
        session.config = {}
        client = Mock()
        client.config = {}

        result = _resolve_dataforseo_modules(session, client)

        self.assertEqual([], result)

    def test_client_none_uses_global(self):
        """Should handle None client gracefully"""
        session = Mock()
        session.config = {}

        result = _resolve_dataforseo_modules(session, None)

        self.assertIsInstance(result, list)


class ChatServiceToolMessagesTestCase(TestCase):
    """Test cases for ChatService handling tool messages in history"""

    def test_build_messages_with_tool_history(self):
        """Should include tool messages from conversation history"""
        history = [
            {"role": "user", "content": "Search for python"},
            {
                "role": "assistant",
                "content": "Let me search.",
                "tool_calls": [
                    {
                        "id": "toolu_123",
                        "name": "serp_google_organic_live",
                        "input": {"keyword": "python"},
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "toolu_123",
                "name": "serp_google_organic_live",
                "content": '{"results": []}',
            },
            {"role": "assistant", "content": "Here are the results."},
        ]

        messages = ChatService.build_messages(
            "Tell me more",
            {},
            history,
            None,
            None,
        )

        # Should have system + history messages + current user message
        roles = [m.get("role") for m in messages]
        self.assertIn("system", roles)
        self.assertIn("tool", roles)
        self.assertEqual("user", roles[-1])

    def test_build_messages_preserves_tool_call_metadata(self):
        """Should preserve tool_calls in assistant messages from history"""
        history = [
            {
                "role": "assistant",
                "content": "Searching...",
                "tool_calls": [
                    {
                        "id": "tc_1",
                        "name": "backlinks_summary",
                        "input": {"target": "x.com"},
                    }
                ],
            },
        ]

        messages = ChatService.build_messages("Continue", {}, history, None, None)

        assistant_msgs = [m for m in messages if m.get("role") == "assistant"]
        has_tool_calls = any("tool_calls" in m for m in assistant_msgs)
        self.assertTrue(has_tool_calls)

    def test_build_messages_preserves_tool_result_fields(self):
        """Should preserve tool_call_id and name in tool messages from history"""
        history = [
            {
                "role": "tool",
                "tool_call_id": "tc_1",
                "name": "backlinks_summary",
                "content": '{"data": "test"}',
            },
        ]

        messages = ChatService.build_messages("OK", {}, history, None, None)

        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        self.assertEqual(1, len(tool_msgs))
        self.assertEqual("tc_1", tool_msgs[0]["tool_call_id"])
        self.assertEqual("backlinks_summary", tool_msgs[0]["name"])

    def test_build_messages_without_tool_history(self):
        """Should work normally without tool messages in history"""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        messages = ChatService.build_messages("How are you?", {}, history, None, None)

        roles = [m.get("role") for m in messages]
        self.assertNotIn("tool", roles)
        self.assertEqual("user", roles[-1])
