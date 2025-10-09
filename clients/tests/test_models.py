"""Test cases for Client model"""

from django.test import TestCase
from model_bakery import baker

from clients.models import Client


class ClientModelTestCase(TestCase):
    """Test cases for Client model"""

    def test_client_creation(self):
        """Should create client with auto-generated fields"""
        # Arrange & Act
        client = Client.objects.create(name="Test Client", email="test@example.com")

        # Assert
        self.assertIsNotNone(client.id)
        self.assertIsNotNone(client.api_key)
        self.assertTrue(client.api_key.startswith("cb_"))
        self.assertEqual("Test Client", client.name)
        self.assertEqual("test@example.com", client.email)
        self.assertTrue(client.is_active)
        self.assertIsNotNone(client.created_at)
        self.assertIsNotNone(client.updated_at)

    def test_client_creation_with_baker(self):
        """Should create client using model_bakery"""
        # Arrange & Act
        client = baker.make(Client, api_key="", _save_kwargs={"force_insert": True})

        # Assert
        self.assertIsNotNone(client.id)
        self.assertIsNotNone(client.api_key)
        self.assertTrue(client.api_key.startswith("cb_"))
        self.assertTrue(client.is_active)

    def test_client_api_key_auto_generation(self):
        """Should auto-generate API key with cb_ prefix on creation"""
        # Arrange & Act
        client = Client.objects.create(name="Test", email="test@example.com")

        # Assert
        self.assertIsNotNone(client.api_key)
        self.assertTrue(client.api_key.startswith("cb_"))
        self.assertGreater(len(client.api_key), 50)  # Should be long and secure

    def test_client_api_key_uniqueness(self):
        """Should generate unique API keys for different clients"""
        # Arrange & Act
        client1 = Client.objects.create(name="Client 1", email="client1@example.com")
        client2 = Client.objects.create(name="Client 2", email="client2@example.com")

        # Assert
        self.assertNotEqual(client1.api_key, client2.api_key)

    def test_client_email_uniqueness(self):
        """Should enforce unique email constraint"""
        # Arrange
        Client.objects.create(name="Client 1", email="test@example.com")

        # Act & Assert
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            Client.objects.create(name="Client 2", email="test@example.com")

    def test_client_default_config(self):
        """Should have empty dict as default config"""
        # Arrange & Act
        client = Client.objects.create(name="Test", email="test@example.com")

        # Assert
        self.assertEqual({}, client.config)
        self.assertIsInstance(client.config, dict)

    def test_client_with_custom_config(self):
        """Should accept custom config on creation"""
        # Arrange
        config = {
            "bot_name": "My Bot",
            "primary_color": "#ff0000",
            "whitelisted_domains": ["https://example.com"],
        }

        # Act
        client = Client.objects.create(
            name="Test", email="test@example.com", config=config
        )

        # Assert
        self.assertEqual(config, client.config)
        self.assertEqual("My Bot", client.config["bot_name"])

    def test_client_str_representation(self):
        """Should return client name as string representation"""
        # Arrange
        client = Client.objects.create(name="Test Client", email="test@example.com")

        # Act
        result = str(client)

        # Assert
        self.assertEqual("Test Client", result)

    def test_client_is_active_default_true(self):
        """Should have is_active=True by default"""
        # Arrange & Act
        client = Client.objects.create(name="Test", email="test@example.com")

        # Assert
        self.assertTrue(client.is_active)

    def test_client_can_be_deactivated(self):
        """Should allow setting is_active to False"""
        # Arrange
        client = Client.objects.create(name="Test", email="test@example.com")

        # Act
        client.is_active = False
        client.save()

        # Assert
        refreshed_client = Client.objects.get(id=client.id)
        self.assertFalse(refreshed_client.is_active)

    def test_generate_api_key_static_method(self):
        """Should generate API key with correct format"""
        # Act
        api_key = Client.generate_api_key()

        # Assert
        self.assertIsInstance(api_key, str)
        self.assertTrue(api_key.startswith("cb_"))
        self.assertGreater(len(api_key), 50)

    def test_regenerate_api_key_method(self):
        """Should regenerate API key and update database"""
        # Arrange
        client = Client.objects.create(name="Test", email="test@example.com")
        old_api_key = client.api_key

        # Act
        new_api_key = client.regenerate_api_key()

        # Assert
        self.assertNotEqual(old_api_key, new_api_key)
        self.assertTrue(new_api_key.startswith("cb_"))
        # Verify it's saved in database
        refreshed_client = Client.objects.get(id=client.id)
        self.assertEqual(new_api_key, refreshed_client.api_key)

    def test_regenerate_api_key_returns_new_key(self):
        """Should return the new API key"""
        # Arrange
        client = Client.objects.create(name="Test", email="test@example.com")

        # Act
        returned_key = client.regenerate_api_key()

        # Assert
        self.assertEqual(client.api_key, returned_key)

    def test_client_ordering(self):
        """Should order clients by created_at descending"""
        # Arrange
        import time

        client1 = Client.objects.create(name="First", email="first@example.com")
        time.sleep(0.01)  # Small delay to ensure different timestamps
        client2 = Client.objects.create(name="Second", email="second@example.com")

        # Act
        clients = list(Client.objects.all())

        # Assert
        self.assertEqual(client2.id, clients[0].id)  # Most recent first
        self.assertEqual(client1.id, clients[1].id)

    def test_client_has_api_key_index(self):
        """Should have database index on api_key field"""
        # This test verifies the model meta configuration
        # Arrange & Act
        indexes = Client._meta.indexes

        # Assert
        api_key_indexes = [idx for idx in indexes if "api_key" in idx.fields]
        self.assertGreater(len(api_key_indexes), 0)

    def test_client_has_is_active_index(self):
        """Should have database index on is_active field"""
        # Arrange & Act
        indexes = Client._meta.indexes

        # Assert
        is_active_indexes = [idx for idx in indexes if "is_active" in idx.fields]
        self.assertGreater(len(is_active_indexes), 0)

    def test_client_updated_at_changes_on_save(self):
        """Should update updated_at timestamp on save"""
        # Arrange
        import time

        client = Client.objects.create(name="Test", email="test@example.com")
        original_updated_at = client.updated_at

        # Act
        time.sleep(0.01)  # Small delay
        client.name = "Updated Name"
        client.save()

        # Assert
        self.assertNotEqual(original_updated_at, client.updated_at)
        self.assertGreater(client.updated_at, original_updated_at)

    def test_client_config_json_field_accepts_nested_data(self):
        """Should accept nested JSON data in config"""
        # Arrange
        config = {
            "branding": {"color": "#ff0000", "logo": "url"},
            "features": {"chat": True, "voice": False},
            "nested": {"deep": {"data": [1, 2, 3]}},
        }

        # Act
        client = Client.objects.create(
            name="Test", email="test@example.com", config=config
        )

        # Assert
        refreshed = Client.objects.get(id=client.id)
        self.assertEqual(config, refreshed.config)
        self.assertEqual("#ff0000", refreshed.config["branding"]["color"])

    def test_client_api_key_not_editable_in_admin(self):
        """Should have api_key field as non-editable"""
        # Arrange & Act
        api_key_field = Client._meta.get_field("api_key")

        # Assert
        self.assertFalse(api_key_field.editable)

    def test_client_id_uuid_not_editable(self):
        """Should have id field as non-editable UUID"""
        # Arrange & Act
        id_field = Client._meta.get_field("id")

        # Assert
        self.assertFalse(id_field.editable)
        self.assertEqual("UUIDField", id_field.__class__.__name__)

    def test_multiple_clients_different_configs(self):
        """Should allow different configs for different clients"""
        # Arrange & Act
        client1 = Client.objects.create(
            name="Client 1",
            email="client1@example.com",
            config={"theme": "dark", "lang": "en"},
        )
        client2 = Client.objects.create(
            name="Client 2",
            email="client2@example.com",
            config={"theme": "light", "lang": "es"},
        )

        # Assert
        self.assertEqual("dark", client1.config["theme"])
        self.assertEqual("light", client2.config["theme"])
        self.assertNotEqual(client1.config, client2.config)
