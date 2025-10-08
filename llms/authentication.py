from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

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
