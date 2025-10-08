from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission

from clients.models import Client


class APIKeyAuthentication(BaseAuthentication):
    """
    API Key authentication for client identification.
    Clients send X-API-Key header with their unique API key.
    """

    def authenticate(self, request):
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return None  # No API key provided, skip this authentication method

        try:
            client = Client.objects.get(api_key=api_key)

            if not client.is_active:
                raise AuthenticationFailed("Client account is inactive")

            # Return (user, auth) tuple. We use None for user since we're doing client-based auth
            return (None, client)

        except Client.DoesNotExist:
            raise AuthenticationFailed("Invalid API key")


class IsClientAuthenticated(BasePermission):
    """
    Permission class that requires a valid client authentication.
    Used to enforce X-API-Key authentication on chat endpoints.
    """

    def has_permission(self, request, view):
        # request.auth contains the client object if authenticated via APIKeyAuthentication
        return request.auth is not None
