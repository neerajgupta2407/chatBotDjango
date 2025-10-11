import logging

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import TemplateView
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
<script src="{base_url}/widget/chatbot.js?apiKey={client.api_key}"></script>"""

        return Response(
            {
                "html": embed_code,
                "instructions": "Paste this code before the closing </body> tag on your website.",
                "api_key": client.api_key,
            }
        )


class WidgetJavaScriptView(APIView):
    """Serve chatbot.js dynamically with client configuration embedded"""

    authentication_classes = []  # Disable DRF authentication for this view
    permission_classes = []  # Allow public access

    def get(self, request):
        api_key = request.GET.get("apiKey")
        user_identifier = request.GET.get("userIdentifier")

        # Default configuration
        context = {
            "api_key": api_key or "",
            "api_base_url": request.build_absolute_uri("/")[:-1],
            "WIDGET_BASE_URL": settings.WIDGET_BASE_URL,
            "bot_name": "AI Assistant",
            "bot_color": "#667eea",
            "bot_msg_bg_color": "#667eea",
            "bot_icon_url": "",
            "powered_by_text": "Powered by AI",
            "user_identifier": user_identifier or "",
        }

        # Try to load client-specific configuration
        if api_key:
            try:
                client = Client.objects.get(api_key=api_key, is_active=True)
                config = client.config

                # Override defaults with client configuration
                context.update(
                    {
                        "bot_name": config.get("bot_name", context["bot_name"]),
                        "bot_color": config.get("primary_color", context["bot_color"]),
                        "bot_msg_bg_color": config.get(
                            "bot_message_bg_color", context["bot_msg_bg_color"]
                        ),
                        "bot_icon_url": config.get("bot_icon_url", ""),
                        "powered_by_text": config.get(
                            "powered_by_text", context["powered_by_text"]
                        ),
                    }
                )

                logger.info(f"Serving widget JS for client: {client.name}")

            except Client.DoesNotExist:
                logger.warning(f"Invalid API key in widget JS request: {api_key}")

        # Render JavaScript template
        javascript_content = render_to_string("widget/chatbot.js", context)

        # Return as JavaScript file
        response = HttpResponse(
            javascript_content, content_type="application/javascript"
        )
        # Add cache control headers
        response["Cache-Control"] = "public, max-age=300"  # Cache for 5 minutes
        return response


class WidgetHTMLView(TemplateView):
    """Serve chatbot.html with WIDGET_BASE_URL injected"""

    template_name = "widget/chatbot.html"
    content_type = "text/html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["WIDGET_BASE_URL"] = settings.WIDGET_BASE_URL
        return context
