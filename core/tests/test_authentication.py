from django.test import RequestFactory, TestCase
from rest_framework.exceptions import AuthenticationFailed

from clients.models import Client
from core.authentication import APIKeyAuthentication, IsClientAuthenticated


class APIKeyAuthenticationTestCase(TestCase):
    """Test cases for APIKeyAuthentication class"""

    def setUp(self):
        """Set up test client and authentication instance"""
        self.factory = RequestFactory()
        self.auth = APIKeyAuthentication()
        self.client = Client.objects.create(
            name="Test Client",
            email="test@example.com",
            config={"whitelisted_domains": ["https://example.com", "https://test.com"]},
        )

    def test_authenticate_with_valid_api_key(self):
        """Should authenticate successfully with valid API key"""
        request = self.factory.get("/api/test")
        request.META["HTTP_X_API_KEY"] = self.client.api_key

        user, auth = self.auth.authenticate(request)

        self.assertIsNone(user)  # User should be None for client-based auth
        self.assertEqual(self.client, auth)

    def test_authenticate_without_api_key(self):
        """Should return None when no API key is provided"""
        request = self.factory.get("/api/test")

        result = self.auth.authenticate(request)

        self.assertIsNone(result)

    def test_authenticate_with_invalid_api_key(self):
        """Should raise AuthenticationFailed with invalid API key"""
        request = self.factory.get("/api/test")
        request.META["HTTP_X_API_KEY"] = "cb_invalid_key"

        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)

        self.assertEqual("Invalid API key", str(context.exception.detail))

    def test_authenticate_with_inactive_client(self):
        """Should raise AuthenticationFailed when client is inactive"""
        self.client.is_active = False
        self.client.save()

        request = self.factory.get("/api/test")
        request.META["HTTP_X_API_KEY"] = self.client.api_key

        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)

        self.assertEqual("Client account is inactive", str(context.exception.detail))

    def test_authenticate_header_case_insensitive(self):
        """Should handle API key header with different casing"""
        request = self.factory.get("/api/test")
        # Django normalizes headers, so X-API-Key becomes HTTP_X_API_KEY
        request.META["HTTP_X_API_KEY"] = self.client.api_key

        user, auth = self.auth.authenticate(request)

        self.assertIsNone(user)
        self.assertEqual(self.client, auth)


class IsClientAuthenticatedTestCase(TestCase):
    """Test cases for IsClientAuthenticated permission class"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.permission = IsClientAuthenticated()
        self.client = Client.objects.create(
            name="Test Client", email="test@example.com"
        )

    def test_has_permission_with_authenticated_client(self):
        """Should return True when client is authenticated"""
        request = self.factory.get("/api/test")
        request.auth = self.client  # Simulates authenticated client

        has_perm = self.permission.has_permission(request, None)

        self.assertTrue(has_perm)

    def test_has_permission_without_authentication(self):
        """Should return False when no client is authenticated"""
        request = self.factory.get("/api/test")
        request.auth = None  # No authentication

        has_perm = self.permission.has_permission(request, None)

        self.assertFalse(has_perm)
