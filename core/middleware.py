from urllib.parse import urlparse

from django.conf import settings
from django.http import JsonResponse

from clients.models import Client


class DomainWhitelistMiddleware:
    """
    Validates that requests come from whitelisted domains for each client.
    Checks Origin or Referer header against client's whitelisted_domains config.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip validation for admin, health check, and static files
        exempt_paths = ["/admin/", "/health", "/static/", "/media/"]
        if any(request.path.startswith(path) for path in exempt_paths):
            return self.get_response(request)

        # Manually authenticate the client from X-API-Key header
        # (Middleware runs before view-level authentication)
        api_key = request.headers.get("X-API-Key")
        client = None

        if api_key:
            try:
                client = Client.objects.get(api_key=api_key, is_active=True)
            except Client.DoesNotExist:
                pass  # Will be handled by view authentication

        # If no client authenticated, let it pass (will be handled by view permissions)
        if not client:
            return self.get_response(request)

        # Get origin from headers
        origin = request.headers.get("Origin") or request.headers.get("Referer")

        # If no origin, reject (likely direct API call, not from browser)
        if not origin:
            return JsonResponse(
                {
                    "error": "Origin header required",
                    "detail": "Requests must originate from a whitelisted domain",
                },
                status=403,
            )

        # Extract domain from origin
        parsed = urlparse(origin)
        request_domain = f"{parsed.scheme}://{parsed.netloc}"

        # Get whitelisted domains from client config
        whitelisted_domains = client.config.get("whitelisted_domains", [])

        # Allow localhost for development
        if request_domain.startswith("http://localhost") or request_domain.startswith(
            "http://127.0.0.1"
        ):
            if getattr(settings, "DEBUG", False):
                return self.get_response(request)

        # Check if request domain is whitelisted
        is_whitelisted = False
        for allowed_domain in whitelisted_domains:
            # Support wildcard subdomains
            if allowed_domain.startswith("*."):
                base_domain = allowed_domain[2:]  # Remove *.
                if request_domain.endswith(base_domain):
                    is_whitelisted = True
                    break
            # Exact match or starts with
            elif request_domain == allowed_domain or request_domain.startswith(
                allowed_domain
            ):
                is_whitelisted = True
                break

        if not is_whitelisted:
            return JsonResponse(
                {
                    "error": "Domain not whitelisted",
                    "domain": request_domain,
                    "whitelisted_domains": whitelisted_domains,
                },
                status=403,
            )

        return self.get_response(request)
