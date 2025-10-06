import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Client
from .serializers import ClientConfigSerializer, ClientSerializer

logger = logging.getLogger(__name__)


class ClientConfigView(APIView):
    """Get and update authenticated client's configuration"""

    def get(self, request):
        client = request.auth  # Client object from APIKeyAuthentication

        if not client:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(
            {"client_id": str(client.id), "name": client.name, "config": client.config}
        )

    def put(self, request):
        """Update client configuration"""
        client = request.auth

        if not client:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = ClientConfigSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_config = serializer.validated_data["config"]

        # Merge with existing config
        client.config = {**client.config, **new_config}
        client.save()

        logger.info(f"Client {client.name} updated configuration")

        return Response(
            {
                "client_id": str(client.id),
                "config": client.config,
                "message": "Configuration updated successfully",
            }
        )


class WidgetConfigView(APIView):
    """Get widget-specific configuration for embedding"""

    def get(self, request):
        client = request.auth

        if not client:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        config = client.config

        # Return only widget-relevant settings
        return Response(
            {
                "branding": {
                    "logo_url": config.get("logo_url"),
                    "primary_color": config.get("primary_color", "#667eea"),
                    "bot_message_bg_color": config.get(
                        "bot_message_bg_color", "#667eea"
                    ),
                    "bot_icon_url": config.get("bot_icon_url"),
                    "bot_name": config.get("bot_name", "AI Assistant"),
                    "powered_by_text": config.get("powered_by_text", "Powered by AI"),
                },
                "layout": {
                    "widget_position": config.get("widget_position", "bottom-right"),
                    "widget_size": config.get("widget_size", "medium"),
                    "widget_offset": config.get("widget_offset", {"x": 20, "y": 20}),
                    "initial_state": config.get("initial_state", "minimized"),
                    "theme": config.get("theme", "light"),
                },
                "features": {
                    "enable_file_upload": config.get("enable_file_upload", True),
                    "enable_json_upload": config.get("enable_json_upload", True),
                    "enable_csv_upload": config.get("enable_csv_upload", True),
                    "max_file_size_mb": config.get("max_file_size_mb", 10),
                },
            }
        )


class RegenerateAPIKeyView(APIView):
    """Regenerate client's API key"""

    def post(self, request):
        client = request.auth

        if not client:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        new_api_key = client.regenerate_api_key()

        logger.warning(f"API key regenerated for client: {client.name}")

        return Response(
            {
                "api_key": new_api_key,
                "message": "API key regenerated successfully. Update your widget code with the new key.",
            }
        )


class WidgetEmbedCodeView(APIView):
    """Get HTML embed code for widget"""

    def get(self, request):
        client = request.auth

        if not client:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Generate embed code
        base_url = request.build_absolute_uri("/")[:-1]  # Remove trailing slash
        embed_code = f"""<!-- Chatbot Widget -->
<script src="{base_url}/static/widget/chatbot.js" data-api-key="{client.api_key}"></script>"""

        return Response(
            {
                "html": embed_code,
                "instructions": "Paste this code before the closing </body> tag on your website.",
                "api_key": client.api_key,
            }
        )
