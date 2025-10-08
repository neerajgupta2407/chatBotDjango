from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.models import Session
from core.authentication import APIKeyAuthentication, IsClientAuthenticated


class SessionCreateView(APIView):
    """Create a new session"""

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsClientAuthenticated]

    def post(self, request):
        client = request.auth  # Get client from API key authentication
        config = request.data.get("config", {})
        user_identifier = request.data.get("user_identifier")

        # Use client's configuration as base
        client_config = {
            "botName": client.config.get("bot_name", settings.BOT_NAME),
            "poweredBy": client.config.get("powered_by_text", settings.BOT_POWERED_BY),
            "botColor": client.config.get("primary_color", settings.BOT_COLOR),
            "botIcon": client.config.get("bot_icon_url", settings.BOT_ICON),
            "botMsgBgColor": client.config.get(
                "bot_message_bg_color", settings.BOT_MSG_BG_COLOR
            ),
        }
        merged_config = {**client_config, **config}

        # Create session linked to client
        session = Session.objects.create(
            client=client, config=merged_config, user_identifier=user_identifier
        )

        return Response(
            {
                "sessionId": str(session.id),
                "config": session.config,
                "status": "created",
                "timestamp": session.created_at.isoformat(),
            },
            status=status.HTTP_201_CREATED,
        )


class SessionDetailView(APIView):
    """Get session data"""

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsClientAuthenticated]

    def get(self, request, session_id):
        client = request.auth

        try:
            session = Session.objects.get(id=session_id, client=client)
            session.update_activity()

            return Response(
                {
                    "sessionId": str(session.id),
                    "messages": session.messages,
                    "config": session.config,
                    "createdAt": session.created_at.isoformat(),
                    "lastActivity": session.last_activity.isoformat(),
                }
            )
        except Session.DoesNotExist:
            return Response(
                {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
            )


class SessionConfigUpdateView(APIView):
    """Update session configuration"""

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsClientAuthenticated]

    def put(self, request, session_id):
        client = request.auth

        try:
            session = Session.objects.get(id=session_id, client=client)
            config = request.data.get("config", {})

            session.config = {**session.config, **config}
            session.save()

            return Response(
                {
                    "sessionId": str(session.id),
                    "config": session.config,
                    "status": "updated",
                }
            )
        except Session.DoesNotExist:
            return Response(
                {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
            )


class SessionStatsView(APIView):
    """Get session statistics"""

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsClientAuthenticated]

    def get(self, request):
        from datetime import timedelta

        client = request.auth

        # Show only authenticated client's stats
        sessions_query = Session.objects.filter(client=client)

        total_sessions = sessions_query.count()
        five_minutes_ago = timezone.now() - timedelta(minutes=5)
        recently_active = sessions_query.filter(
            last_activity__gte=five_minutes_ago
        ).count()

        return Response(
            {
                "totalSessions": total_sessions,
                "recentlyActive": recently_active,
                "timestamp": timezone.now().isoformat(),
            }
        )


class BotConfigView(APIView):
    """Get bot configuration"""

    def get(self, request):
        bot_config = {
            "botName": settings.BOT_NAME,
            "poweredBy": settings.BOT_POWERED_BY,
            "botColor": settings.BOT_COLOR,
            "botIcon": settings.BOT_ICON,
            "botMsgBgColor": settings.BOT_MSG_BG_COLOR,
        }

        return Response(bot_config)


class SessionUserStatsView(APIView):
    """Get session statistics grouped by user identifier"""

    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsClientAuthenticated]

    def get(self, request):
        from django.db.models import Count

        client = request.auth

        # Show only authenticated client's stats
        sessions_query = Session.objects.filter(client=client)

        # Group sessions by user_identifier and count
        user_stats = (
            sessions_query.filter(user_identifier__isnull=False)
            .values("user_identifier")
            .annotate(session_count=Count("id"))
            .order_by("-session_count")
        )

        # Format response
        stats_dict = {
            stat["user_identifier"]: stat["session_count"] for stat in user_stats
        }

        # Also include total stats
        total_sessions = sessions_query.count()
        sessions_with_user = sessions_query.filter(
            user_identifier__isnull=False
        ).count()
        sessions_without_user = total_sessions - sessions_with_user

        return Response(
            {
                "userStats": stats_dict,
                "summary": {
                    "totalSessions": total_sessions,
                    "sessionsWithUser": sessions_with_user,
                    "sessionsWithoutUser": sessions_without_user,
                    "uniqueUsers": len(stats_dict),
                },
                "timestamp": timezone.now().isoformat(),
            }
        )
