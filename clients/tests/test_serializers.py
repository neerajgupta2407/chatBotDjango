"""Test cases for Client serializers"""

from django.test import TestCase
from model_bakery import baker

from clients.models import Client
from clients.serializers import ClientConfigSerializer, ClientSerializer


class ClientSerializerTestCase(TestCase):
    """Test cases for ClientSerializer"""

    def setUp(self):
        """Set up test data"""
        self.client = baker.make(
            Client,
            name="Test Client",
            email="test@example.com",
            config={"bot_name": "Test Bot"},
        )

    def test_serializer_contains_expected_fields(self):
        """Should contain all specified fields"""
        # Arrange
        serializer = ClientSerializer(instance=self.client)

        # Act
        data = serializer.data

        # Assert
        self.assertIn("id", data)
        self.assertIn("name", data)
        self.assertIn("email", data)
        self.assertIn("api_key", data)
        self.assertIn("config", data)
        self.assertIn("is_active", data)
        self.assertIn("created_at", data)

    def test_serializer_field_values(self):
        """Should serialize field values correctly"""
        # Arrange
        serializer = ClientSerializer(instance=self.client)

        # Act
        data = serializer.data

        # Assert
        self.assertEqual(str(self.client.id), data["id"])
        self.assertEqual("Test Client", data["name"])
        self.assertEqual("test@example.com", data["email"])
        self.assertEqual(self.client.api_key, data["api_key"])
        self.assertEqual({"bot_name": "Test Bot"}, data["config"])
        self.assertTrue(data["is_active"])

    def test_serializer_read_only_fields(self):
        """Should have id, api_key, and created_at as read-only"""
        # Arrange
        serializer = ClientSerializer()

        # Act
        read_only_fields = serializer.Meta.read_only_fields

        # Assert
        self.assertIn("id", read_only_fields)
        self.assertIn("api_key", read_only_fields)
        self.assertIn("created_at", read_only_fields)

    def test_serializer_does_not_update_read_only_fields(self):
        """Should not update read-only fields"""
        # Arrange
        original_api_key = self.client.api_key
        data = {
            "name": "Updated Name",
            "api_key": "cb_attempt_to_change",
            "config": {},
        }

        # Act
        serializer = ClientSerializer(instance=self.client, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()

        # Assert
        refreshed = Client.objects.get(id=self.client.id)
        self.assertEqual("Updated Name", refreshed.name)
        self.assertEqual(original_api_key, refreshed.api_key)  # Should not change

    def test_serializer_handles_empty_config(self):
        """Should handle empty config dictionary"""
        # Arrange
        client = baker.make(Client, config={})
        serializer = ClientSerializer(instance=client)

        # Act
        data = serializer.data

        # Assert
        self.assertEqual({}, data["config"])

    def test_serializer_handles_nested_config(self):
        """Should serialize nested config data"""
        # Arrange
        client = baker.make(
            Client,
            config={
                "branding": {"color": "#ff0000", "logo": "url"},
                "features": {"enabled": True},
            },
        )
        serializer = ClientSerializer(instance=client)

        # Act
        data = serializer.data

        # Assert
        self.assertEqual("#ff0000", data["config"]["branding"]["color"])
        self.assertTrue(data["config"]["features"]["enabled"])


class ClientConfigSerializerTestCase(TestCase):
    """Test cases for ClientConfigSerializer"""

    def test_serializer_validates_valid_config(self):
        """Should validate correct JSON config"""
        # Arrange
        data = {"config": {"bot_name": "My Bot", "theme": "dark"}}

        # Act
        serializer = ClientConfigSerializer(data=data)

        # Assert
        self.assertTrue(serializer.is_valid())
        self.assertEqual(data["config"], serializer.validated_data["config"])

    def test_serializer_validates_empty_config(self):
        """Should validate empty config dictionary"""
        # Arrange
        data = {"config": {}}

        # Act
        serializer = ClientConfigSerializer(data=data)

        # Assert
        self.assertTrue(serializer.is_valid())

    def test_serializer_validates_nested_config(self):
        """Should validate nested JSON config"""
        # Arrange
        data = {
            "config": {
                "branding": {"color": "#ff0000", "logo": "url"},
                "features": {"chat": True, "voice": False},
            }
        }

        # Act
        serializer = ClientConfigSerializer(data=data)

        # Assert
        self.assertTrue(serializer.is_valid())
        self.assertEqual(data["config"], serializer.validated_data["config"])

    def test_serializer_rejects_non_dict_config(self):
        """Should reject config that is not a dictionary"""
        # Arrange
        invalid_configs = [
            {"config": "string"},
            {"config": 123},
            {"config": ["list"]},
            {"config": None},
        ]

        # Act & Assert
        for invalid_data in invalid_configs:
            serializer = ClientConfigSerializer(data=invalid_data)
            self.assertFalse(serializer.is_valid())
            self.assertIn("config", serializer.errors)

    def test_serializer_error_message_for_invalid_config(self):
        """Should provide clear error message for invalid config"""
        # Arrange
        data = {"config": "not a dict"}

        # Act
        serializer = ClientConfigSerializer(data=data)
        serializer.is_valid()

        # Assert
        self.assertIn("config", serializer.errors)
        error_message = str(serializer.errors["config"][0])
        self.assertIn("JSON object", error_message)

    def test_serializer_requires_config_field(self):
        """Should require config field"""
        # Arrange
        data = {}

        # Act
        serializer = ClientConfigSerializer(data=data)

        # Assert
        self.assertFalse(serializer.is_valid())
        self.assertIn("config", serializer.errors)

    def test_serializer_accepts_config_with_arrays(self):
        """Should accept config with array values"""
        # Arrange
        data = {
            "config": {
                "whitelisted_domains": ["https://example.com", "https://test.com"],
                "allowed_ips": ["192.168.1.1", "10.0.0.1"],
            }
        }

        # Act
        serializer = ClientConfigSerializer(data=data)

        # Assert
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            2, len(serializer.validated_data["config"]["whitelisted_domains"])
        )

    def test_serializer_accepts_config_with_boolean_values(self):
        """Should accept config with boolean values"""
        # Arrange
        data = {
            "config": {
                "enable_chat": True,
                "enable_voice": False,
                "debug_mode": True,
            }
        }

        # Act
        serializer = ClientConfigSerializer(data=data)

        # Assert
        self.assertTrue(serializer.is_valid())
        self.assertTrue(serializer.validated_data["config"]["enable_chat"])
        self.assertFalse(serializer.validated_data["config"]["enable_voice"])

    def test_serializer_accepts_config_with_number_values(self):
        """Should accept config with numeric values"""
        # Arrange
        data = {
            "config": {
                "max_file_size_mb": 10,
                "timeout_seconds": 30.5,
                "max_retries": 3,
            }
        }

        # Act
        serializer = ClientConfigSerializer(data=data)

        # Assert
        self.assertTrue(serializer.is_valid())
        self.assertEqual(10, serializer.validated_data["config"]["max_file_size_mb"])
        self.assertEqual(30.5, serializer.validated_data["config"]["timeout_seconds"])

    def test_serializer_accepts_deeply_nested_config(self):
        """Should accept deeply nested config structures"""
        # Arrange
        data = {
            "config": {
                "level1": {
                    "level2": {
                        "level3": {"level4": {"value": "deep"}},
                        "other": "data",
                    }
                }
            }
        }

        # Act
        serializer = ClientConfigSerializer(data=data)

        # Assert
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            "deep",
            serializer.validated_data["config"]["level1"]["level2"]["level3"]["level4"][
                "value"
            ],
        )
