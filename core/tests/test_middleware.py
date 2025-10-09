import json
from unittest.mock import Mock

from django.http import JsonResponse
from django.test import RequestFactory, TestCase, override_settings

from clients.models import Client
from core.middleware import DomainWhitelistMiddleware


class DomainWhitelistMiddlewareTestCase(TestCase):
    """Test cases for DomainWhitelistMiddleware"""

    def setUp(self):
        """Set up test client and middleware"""
        self.factory = RequestFactory()
        self.client = Client.objects.create(
            name="Test Client",
            email="test@example.com",
            config={
                "whitelisted_domains": [
                    "https://example.com",
                    "https://app.example.com",
                    "*.wildcard.com",
                ]
            },
        )
        self.get_response = Mock(return_value=JsonResponse({"success": True}))
        self.middleware = DomainWhitelistMiddleware(self.get_response)

    def test_exempt_path_admin(self):
        """Should skip validation for /admin/ path"""
        request = self.factory.get("/admin/")
        request.auth = self.client

        response = self.middleware(request)

        self.get_response.assert_called_once_with(request)

    def test_exempt_path_health(self):
        """Should skip validation for /health path"""
        request = self.factory.get("/health")
        request.auth = self.client

        response = self.middleware(request)

        self.get_response.assert_called_once_with(request)

    def test_exempt_path_static(self):
        """Should skip validation for /static/ path"""
        request = self.factory.get("/static/css/style.css")
        request.auth = self.client

        response = self.middleware(request)

        self.get_response.assert_called_once_with(request)

    def test_exempt_path_media(self):
        """Should skip validation for /media/ path"""
        request = self.factory.get("/media/uploads/file.jpg")
        request.auth = self.client

        response = self.middleware(request)

        self.get_response.assert_called_once_with(request)

    def test_no_client_authentication(self):
        """Should pass through when no client is authenticated"""
        request = self.factory.get("/api/test")
        request.auth = None

        response = self.middleware(request)

        self.get_response.assert_called_once_with(request)

    def test_missing_origin_header(self):
        """Should return 403 when Origin/Referer header is missing"""
        request = self.factory.get("/api/test")
        request.auth = self.client

        response = self.middleware(request)

        self.assertEqual(403, response.status_code)
        response_data = json.loads(response.content)
        self.assertIn("Origin header required", response_data["error"])

    def test_whitelisted_exact_domain(self):
        """Should allow request from exact whitelisted domain"""
        request = self.factory.get("/api/test")
        request.auth = self.client
        request.META["HTTP_ORIGIN"] = "https://example.com"

        response = self.middleware(request)

        self.get_response.assert_called_once_with(request)

    def test_whitelisted_subdomain(self):
        """Should allow request from whitelisted subdomain"""
        request = self.factory.get("/api/test")
        request.auth = self.client
        request.META["HTTP_ORIGIN"] = "https://app.example.com"

        response = self.middleware(request)

        self.get_response.assert_called_once_with(request)

    def test_wildcard_domain(self):
        """Should allow request from wildcard domain"""
        request = self.factory.get("/api/test")
        request.auth = self.client
        request.META["HTTP_ORIGIN"] = "https://test.wildcard.com"

        response = self.middleware(request)

        self.get_response.assert_called_once_with(request)

    def test_wildcard_subdomain(self):
        """Should allow request from wildcard subdomain"""
        request = self.factory.get("/api/test")
        request.auth = self.client
        request.META["HTTP_ORIGIN"] = "https://api.test.wildcard.com"

        response = self.middleware(request)

        self.get_response.assert_called_once_with(request)

    def test_non_whitelisted_domain(self):
        """Should return 403 for non-whitelisted domain"""
        request = self.factory.get("/api/test")
        request.auth = self.client
        request.META["HTTP_ORIGIN"] = "https://malicious.com"

        response = self.middleware(request)

        self.assertEqual(403, response.status_code)
        response_data = json.loads(response.content)
        self.assertEqual("Domain not whitelisted", response_data["error"])
        self.assertEqual("https://malicious.com", response_data["domain"])

    def test_referer_header_instead_of_origin(self):
        """Should accept Referer header when Origin is not present"""
        request = self.factory.get("/api/test")
        request.auth = self.client
        request.META["HTTP_REFERER"] = "https://example.com/page"

        response = self.middleware(request)

        self.get_response.assert_called_once_with(request)

    @override_settings(DEBUG=True)
    def test_localhost_allowed_in_debug_mode(self):
        """Should allow localhost in DEBUG mode"""
        request = self.factory.get("/api/test")
        request.auth = self.client
        request.META["HTTP_ORIGIN"] = "http://localhost:3000"

        response = self.middleware(request)

        self.get_response.assert_called_once_with(request)

    @override_settings(DEBUG=True)
    def test_127_0_0_1_allowed_in_debug_mode(self):
        """Should allow 127.0.0.1 in DEBUG mode"""
        request = self.factory.get("/api/test")
        request.auth = self.client
        request.META["HTTP_ORIGIN"] = "http://127.0.0.1:8000"

        response = self.middleware(request)

        self.get_response.assert_called_once_with(request)

    @override_settings(DEBUG=False)
    def test_localhost_blocked_in_production(self):
        """Should block localhost when not in whitelist in production mode"""
        request = self.factory.get("/api/test")
        request.auth = self.client
        request.META["HTTP_ORIGIN"] = "http://localhost:3000"

        response = self.middleware(request)

        self.assertEqual(403, response.status_code)

    def test_domain_extraction_from_origin(self):
        """Should correctly extract domain from Origin header with path"""
        request = self.factory.get("/api/test")
        request.auth = self.client
        request.META["HTTP_ORIGIN"] = "https://example.com/some/path?query=param"

        response = self.middleware(request)

        self.get_response.assert_called_once_with(request)

    def test_empty_whitelist_blocks_all(self):
        """Should block all domains when whitelist is empty"""
        client = Client.objects.create(
            name="Client No Whitelist",
            email="nowhitelist@example.com",
            config={"whitelisted_domains": []},
        )
        request = self.factory.get("/api/test")
        request.auth = client
        request.META["HTTP_ORIGIN"] = "https://example.com"

        response = self.middleware(request)

        self.assertEqual(403, response.status_code)

    def test_missing_whitelist_config_blocks_all(self):
        """Should block all domains when whitelist config is missing"""
        client = Client.objects.create(
            name="Client No Config",
            email="noconfig@example.com",
            config={},  # No whitelisted_domains key
        )
        request = self.factory.get("/api/test")
        request.auth = client
        request.META["HTTP_ORIGIN"] = "https://example.com"

        response = self.middleware(request)

        self.assertEqual(403, response.status_code)
