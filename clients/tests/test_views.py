"""Test cases for Client views"""

from unittest.mock import Mock, patch

from django.test import TestCase
from model_bakery import baker
from rest_framework.test import APIClient

from clients.models import Client


class ClientConfigViewTestCase(TestCase):
    """Test cases for ClientConfigView"""

    def setUp(self):
        """Set up test client and data"""
        self.api_client = APIClient()
        self.client_obj = baker.make(
            Client,
            name="Test Client",
            email="test@example.com",
            config={
                "bot_name": "Test Bot",
                "theme": "dark",
                "whitelisted_domains": ["https://testserver"],
            },
            _save_kwargs={"force_insert": True},
        )
        # Add Origin header for middleware
        self.api_client.credentials(HTTP_ORIGIN="https://testserver")

    def test_get_config_with_authentication(self):
        """Should return client config when authenticated"""
        # Arrange
        self.api_client.credentials(
            HTTP_X_API_KEY=self.client_obj.api_key, HTTP_ORIGIN="https://testserver"
        )

        # Act
        response = self.api_client.get("/api/clients/me/config")

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertIn("client_id", response.data)
        self.assertIn("name", response.data)
        self.assertIn("config", response.data)
        self.assertEqual(str(self.client_obj.id), response.data["client_id"])
        self.assertEqual("Test Client", response.data["name"])
        self.assertEqual(self.client_obj.config, response.data["config"])

    def test_get_config_without_authentication(self):
        """Should return 401 when not authenticated"""
        # Act
        response = self.api_client.get("/api/clients/me/config")

        # Assert
        self.assertEqual(401, response.status_code)

    def test_put_config_with_valid_data(self):
        """Should update client config with valid data"""
        # Arrange
        self.api_client.credentials(
            HTTP_X_API_KEY=self.client_obj.api_key, HTTP_ORIGIN="https://testserver"
        )
        new_config = {"primary_color": "#ff0000", "bot_name": "Updated Bot"}

        # Act
        response = self.api_client.put(
            "/api/clients/me/config", {"config": new_config}, format="json"
        )

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertIn("config", response.data)
        self.assertIn("message", response.data)

        # Verify config was merged (not replaced)
        refreshed = Client.objects.get(id=self.client_obj.id)
        self.assertEqual("Updated Bot", refreshed.config["bot_name"])
        self.assertEqual("#ff0000", refreshed.config["primary_color"])
        self.assertEqual("dark", refreshed.config["theme"])  # Original value preserved

    def test_put_config_merges_with_existing(self):
        """Should merge new config with existing config"""
        # Arrange
        self.api_client.credentials(
            HTTP_X_API_KEY=self.client_obj.api_key, HTTP_ORIGIN="https://testserver"
        )
        new_config = {"new_field": "new_value"}

        # Act
        response = self.api_client.put(
            "/api/clients/me/config", {"config": new_config}, format="json"
        )

        # Assert
        self.assertEqual(200, response.status_code)
        refreshed = Client.objects.get(id=self.client_obj.id)
        self.assertEqual("new_value", refreshed.config["new_field"])
        self.assertEqual("Test Bot", refreshed.config["bot_name"])  # Original preserved

    def test_put_config_with_invalid_data(self):
        """Should return 400 with invalid config data"""
        # Arrange
        self.api_client.credentials(
            HTTP_X_API_KEY=self.client_obj.api_key, HTTP_ORIGIN="https://testserver"
        )
        invalid_data = {"config": "not a dict"}

        # Act
        response = self.api_client.put(
            "/api/clients/me/config", invalid_data, format="json"
        )

        # Assert
        self.assertEqual(400, response.status_code)

    def test_put_config_without_authentication(self):
        """Should return 401 when not authenticated"""
        # Arrange
        new_config = {"primary_color": "#ff0000"}

        # Act
        response = self.api_client.put(
            "/api/clients/me/config", {"config": new_config}, format="json"
        )

        # Assert
        self.assertEqual(401, response.status_code)


class WidgetConfigViewTestCase(TestCase):
    """Test cases for WidgetConfigView"""

    def setUp(self):
        """Set up test client and data"""
        self.api_client = APIClient()
        self.client_obj = baker.make(
            Client,
            config={
                "bot_name": "My Bot",
                "primary_color": "#ff0000",
                "bot_message_bg_color": "#00ff00",
                "bot_icon_url": "https://example.com/icon.png",
                "powered_by_text": "Powered by Example",
                "widget_position": "bottom-left",
                "widget_size": "large",
                "widget_offset": {"x": 30, "y": 40},
                "initial_state": "expanded",
                "theme": "dark",
                "enable_file_upload": False,
                "enable_json_upload": True,
                "enable_csv_upload": False,
                "max_file_size_mb": 15,
                "logo_url": "https://example.com/logo.png",
                "whitelisted_domains": ["https://testserver"],
            },
            _save_kwargs={"force_insert": True},
        )

    def test_get_widget_config_with_authentication(self):
        """Should return widget-specific config when authenticated"""
        # Arrange
        self.api_client.credentials(
            HTTP_X_API_KEY=self.client_obj.api_key, HTTP_ORIGIN="https://testserver"
        )

        # Act
        response = self.api_client.get("/api/widget/config")

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertIn("branding", response.data)
        self.assertIn("layout", response.data)
        self.assertIn("features", response.data)

    def test_widget_config_branding_section(self):
        """Should return correct branding configuration"""
        # Arrange
        self.api_client.credentials(
            HTTP_X_API_KEY=self.client_obj.api_key, HTTP_ORIGIN="https://testserver"
        )

        # Act
        response = self.api_client.get("/api/widget/config")

        # Assert
        branding = response.data["branding"]
        self.assertEqual("https://example.com/logo.png", branding["logo_url"])
        self.assertEqual("#ff0000", branding["primary_color"])
        self.assertEqual("#00ff00", branding["bot_message_bg_color"])
        self.assertEqual("https://example.com/icon.png", branding["bot_icon_url"])
        self.assertEqual("My Bot", branding["bot_name"])
        self.assertEqual("Powered by Example", branding["powered_by_text"])

    def test_widget_config_layout_section(self):
        """Should return correct layout configuration"""
        # Arrange
        self.api_client.credentials(
            HTTP_X_API_KEY=self.client_obj.api_key, HTTP_ORIGIN="https://testserver"
        )

        # Act
        response = self.api_client.get("/api/widget/config")

        # Assert
        layout = response.data["layout"]
        self.assertEqual("bottom-left", layout["widget_position"])
        self.assertEqual("large", layout["widget_size"])
        self.assertEqual({"x": 30, "y": 40}, layout["widget_offset"])
        self.assertEqual("expanded", layout["initial_state"])
        self.assertEqual("dark", layout["theme"])

    def test_widget_config_features_section(self):
        """Should return correct features configuration"""
        # Arrange
        self.api_client.credentials(
            HTTP_X_API_KEY=self.client_obj.api_key, HTTP_ORIGIN="https://testserver"
        )

        # Act
        response = self.api_client.get("/api/widget/config")

        # Assert
        features = response.data["features"]
        self.assertFalse(features["enable_file_upload"])
        self.assertTrue(features["enable_json_upload"])
        self.assertFalse(features["enable_csv_upload"])
        self.assertEqual(15, features["max_file_size_mb"])

    def test_widget_config_with_defaults(self):
        """Should return default values for missing config"""
        # Arrange
        client_with_minimal_config = baker.make(
            Client,
            config={"whitelisted_domains": ["https://testserver"]},
            _save_kwargs={"force_insert": True},
        )
        self.api_client.credentials(
            HTTP_X_API_KEY=client_with_minimal_config.api_key,
            HTTP_ORIGIN="https://testserver",
        )

        # Act
        response = self.api_client.get("/api/widget/config")

        # Assert
        self.assertEqual(200, response.status_code)
        branding = response.data["branding"]
        layout = response.data["layout"]
        features = response.data["features"]

        # Check defaults
        self.assertEqual("#667eea", branding["primary_color"])
        self.assertEqual("AI Assistant", branding["bot_name"])
        self.assertEqual("bottom-right", layout["widget_position"])
        self.assertEqual("medium", layout["widget_size"])
        self.assertEqual({"x": 20, "y": 20}, layout["widget_offset"])
        self.assertEqual("minimized", layout["initial_state"])
        self.assertEqual("light", layout["theme"])
        self.assertTrue(features["enable_file_upload"])
        self.assertEqual(10, features["max_file_size_mb"])

    def test_widget_config_without_authentication(self):
        """Should return 401 when not authenticated"""
        # Act
        response = self.api_client.get("/api/widget/config")

        # Assert
        self.assertEqual(401, response.status_code)


class RegenerateAPIKeyViewTestCase(TestCase):
    """Test cases for RegenerateAPIKeyView"""

    def setUp(self):
        """Set up test client and data"""
        self.api_client = APIClient()
        self.client_obj = baker.make(
            Client,
            config={"whitelisted_domains": ["https://testserver"]},
            _save_kwargs={"force_insert": True},
        )

    def test_regenerate_api_key_with_authentication(self):
        """Should regenerate API key when authenticated"""
        # Arrange
        old_api_key = self.client_obj.api_key
        self.api_client.credentials(
            HTTP_X_API_KEY=old_api_key, HTTP_ORIGIN="https://testserver"
        )

        # Act
        response = self.api_client.post("/api/clients/me/regenerate-key")

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertIn("api_key", response.data)
        self.assertIn("message", response.data)

        new_api_key = response.data["api_key"]
        self.assertNotEqual(old_api_key, new_api_key)
        self.assertTrue(new_api_key.startswith("cb_"))

        # Verify in database
        refreshed = Client.objects.get(id=self.client_obj.id)
        self.assertEqual(new_api_key, refreshed.api_key)

    def test_regenerate_api_key_invalidates_old_key(self):
        """Should invalidate old API key after regeneration"""
        # Arrange
        old_api_key = self.client_obj.api_key
        self.api_client.credentials(
            HTTP_X_API_KEY=old_api_key, HTTP_ORIGIN="https://testserver"
        )

        # Act
        response = self.api_client.post("/api/clients/me/regenerate-key")
        new_api_key = response.data["api_key"]

        # Try to use old key
        self.api_client.credentials(
            HTTP_X_API_KEY=old_api_key, HTTP_ORIGIN="https://testserver"
        )
        test_response = self.api_client.get("/api/clients/me/config")

        # Assert
        self.assertEqual(403, test_response.status_code)

        # New key should work
        self.api_client.credentials(
            HTTP_X_API_KEY=new_api_key, HTTP_ORIGIN="https://testserver"
        )
        test_response = self.api_client.get("/api/clients/me/config")
        self.assertEqual(200, test_response.status_code)

    def test_regenerate_api_key_without_authentication(self):
        """Should return 401 when not authenticated"""
        # Act
        response = self.api_client.post("/api/clients/me/regenerate-key")

        # Assert
        self.assertEqual(401, response.status_code)

    @patch("clients.views.logger")
    def test_regenerate_api_key_logs_warning(self, mock_logger):
        """Should log warning when API key is regenerated"""
        # Arrange
        self.api_client.credentials(
            HTTP_X_API_KEY=self.client_obj.api_key, HTTP_ORIGIN="https://testserver"
        )

        # Act
        response = self.api_client.post("/api/clients/me/regenerate-key")

        # Assert
        self.assertEqual(200, response.status_code)
        mock_logger.warning.assert_called_once()
        call_args = str(mock_logger.warning.call_args)
        self.assertIn("API key regenerated", call_args)


class WidgetEmbedCodeViewTestCase(TestCase):
    """Test cases for WidgetEmbedCodeView"""

    def setUp(self):
        """Set up test client and data"""
        self.api_client = APIClient()
        self.client_obj = baker.make(
            Client,
            name="Test Client",
            config={"whitelisted_domains": ["https://testserver"]},
            _save_kwargs={"force_insert": True},
        )

    def test_get_embed_code_with_authentication(self):
        """Should return embed code when authenticated"""
        # Arrange
        self.api_client.credentials(
            HTTP_X_API_KEY=self.client_obj.api_key, HTTP_ORIGIN="https://testserver"
        )

        # Act
        response = self.api_client.get("/api/clients/me/widget-code")

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertIn("html", response.data)
        self.assertIn("instructions", response.data)
        self.assertIn("api_key", response.data)

    def test_embed_code_contains_api_key(self):
        """Should include API key in embed code"""
        # Arrange
        self.api_client.credentials(
            HTTP_X_API_KEY=self.client_obj.api_key, HTTP_ORIGIN="https://testserver"
        )

        # Act
        response = self.api_client.get("/api/clients/me/widget-code")

        # Assert
        html = response.data["html"]
        self.assertIn(self.client_obj.api_key, html)
        self.assertIn("apiKey=", html)

    def test_embed_code_contains_script_tag(self):
        """Should include script tag in embed code"""
        # Arrange
        self.api_client.credentials(
            HTTP_X_API_KEY=self.client_obj.api_key, HTTP_ORIGIN="https://testserver"
        )

        # Act
        response = self.api_client.get("/api/clients/me/widget-code")

        # Assert
        html = response.data["html"]
        self.assertIn("<script", html)
        self.assertIn("</script>", html)
        self.assertIn("/widget/chatbot.js", html)

    def test_embed_code_contains_instructions(self):
        """Should provide clear instructions"""
        # Arrange
        self.api_client.credentials(
            HTTP_X_API_KEY=self.client_obj.api_key, HTTP_ORIGIN="https://testserver"
        )

        # Act
        response = self.api_client.get("/api/clients/me/widget-code")

        # Assert
        instructions = response.data["instructions"]
        self.assertIn("</body>", instructions)
        self.assertIsInstance(instructions, str)
        self.assertGreater(len(instructions), 0)

    def test_embed_code_without_authentication(self):
        """Should return 401 when not authenticated"""
        # Act
        response = self.api_client.get("/api/clients/me/widget-code")

        # Assert
        self.assertEqual(401, response.status_code)


class WidgetJavaScriptViewTestCase(TestCase):
    """Test cases for WidgetJavaScriptView"""

    def setUp(self):
        """Set up test client and data"""
        self.api_client = APIClient()
        self.client_obj = baker.make(
            Client,
            name="Test Client",
            config={
                "bot_name": "Custom Bot",
                "primary_color": "#ff0000",
                "bot_message_bg_color": "#00ff00",
                "bot_icon_url": "https://example.com/icon.png",
                "powered_by_text": "Custom Powered By",
            },
            _save_kwargs={"force_insert": True},
        )

    @patch("clients.views.render_to_string")
    def test_get_widget_js_with_valid_api_key(self, mock_render):
        """Should serve widget JS with client config"""
        # Arrange
        mock_render.return_value = "// JavaScript content"

        # Act
        response = self.api_client.get(
            f"/widget/chatbot.js?apiKey={self.client_obj.api_key}"
        )

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertEqual("application/javascript", response["Content-Type"])
        mock_render.assert_called_once()

        # Check context passed to template
        context = mock_render.call_args[0][1]
        self.assertEqual(self.client_obj.api_key, context["api_key"])
        self.assertEqual("Custom Bot", context["bot_name"])
        self.assertEqual("#ff0000", context["bot_color"])
        self.assertEqual("#00ff00", context["bot_msg_bg_color"])

    @patch("clients.views.render_to_string")
    def test_get_widget_js_with_invalid_api_key(self, mock_render):
        """Should serve default config with invalid API key"""
        # Arrange
        mock_render.return_value = "// JavaScript content"

        # Act
        response = self.api_client.get("/widget/chatbot.js?apiKey=invalid_key")

        # Assert
        self.assertEqual(200, response.status_code)

        # Check context has defaults
        context = mock_render.call_args[0][1]
        self.assertEqual("invalid_key", context["api_key"])
        self.assertEqual("AI Assistant", context["bot_name"])
        self.assertEqual("#667eea", context["bot_color"])

    @patch("clients.views.render_to_string")
    def test_get_widget_js_without_api_key(self, mock_render):
        """Should serve with empty API key and defaults"""
        # Arrange
        mock_render.return_value = "// JavaScript content"

        # Act
        response = self.api_client.get("/widget/chatbot.js")

        # Assert
        self.assertEqual(200, response.status_code)
        context = mock_render.call_args[0][1]
        self.assertEqual("", context["api_key"])
        self.assertEqual("AI Assistant", context["bot_name"])

    @patch("clients.views.render_to_string")
    def test_get_widget_js_with_user_identifier(self, mock_render):
        """Should include user identifier in context"""
        # Arrange
        mock_render.return_value = "// JavaScript content"

        # Act
        response = self.api_client.get(
            f"/widget/chatbot.js?apiKey={self.client_obj.api_key}&userIdentifier=user123"
        )

        # Assert
        self.assertEqual(200, response.status_code)
        context = mock_render.call_args[0][1]
        self.assertEqual("user123", context["user_identifier"])

    def test_get_widget_js_has_cache_headers(self):
        """Should include cache control headers"""
        # Act
        response = self.api_client.get(
            f"/widget/chatbot.js?apiKey={self.client_obj.api_key}"
        )

        # Assert
        self.assertIn("Cache-Control", response)
        self.assertIn("max-age=300", response["Cache-Control"])

    def test_get_widget_js_no_authentication_required(self):
        """Should not require authentication (public endpoint)"""
        # Act
        response = self.api_client.get("/widget/chatbot.js")

        # Assert
        self.assertEqual(200, response.status_code)

    @patch("clients.views.logger")
    @patch("clients.views.render_to_string")
    def test_get_widget_js_logs_success(self, mock_render, mock_logger):
        """Should log when serving widget for valid client"""
        # Arrange
        mock_render.return_value = "// JavaScript content"

        # Act
        response = self.api_client.get(
            f"/widget/chatbot.js?apiKey={self.client_obj.api_key}"
        )

        # Assert
        self.assertEqual(200, response.status_code)
        mock_logger.info.assert_called_once()
        call_args = str(mock_logger.info.call_args)
        self.assertIn("Serving widget JS", call_args)

    @patch("clients.views.logger")
    @patch("clients.views.render_to_string")
    def test_get_widget_js_logs_invalid_key(self, mock_render, mock_logger):
        """Should log warning for invalid API key"""
        # Arrange
        mock_render.return_value = "// JavaScript content"

        # Act
        response = self.api_client.get("/widget/chatbot.js?apiKey=invalid_key")

        # Assert
        self.assertEqual(200, response.status_code)
        mock_logger.warning.assert_called_once()
        call_args = str(mock_logger.warning.call_args)
        self.assertIn("Invalid API key", call_args)

    @patch("clients.views.render_to_string")
    def test_get_widget_js_with_inactive_client(self, mock_render):
        """Should use defaults when client is inactive"""
        # Arrange
        self.client_obj.is_active = False
        self.client_obj.save()
        mock_render.return_value = "// JavaScript content"

        # Act
        response = self.api_client.get(
            f"/widget/chatbot.js?apiKey={self.client_obj.api_key}"
        )

        # Assert
        self.assertEqual(200, response.status_code)
        context = mock_render.call_args[0][1]
        # Should use defaults, not client config
        self.assertEqual("AI Assistant", context["bot_name"])
