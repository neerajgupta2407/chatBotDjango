from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.models import Session


class SessionCreateView(APIView):
    """Create a new session"""

    def post(self, request):
        client = request.auth  # Get client from API key authentication
        config = request.data.get("config", {})
        user_identifier = request.data.get("user_identifier")

        # If client is authenticated, use client's configuration as base
        if client:
            client_config = {
                "botName": client.config.get("bot_name", settings.BOT_NAME),
                "poweredBy": client.config.get(
                    "powered_by_text", settings.BOT_POWERED_BY
                ),
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
        else:
            # Fallback to environment-based configuration for backward compatibility
            bot_config = {
                "botName": settings.BOT_NAME,
                "poweredBy": settings.BOT_POWERED_BY,
                "botColor": settings.BOT_COLOR,
                "botIcon": settings.BOT_ICON,
                "botMsgBgColor": settings.BOT_MSG_BG_COLOR,
            }
            merged_config = {**bot_config, **config}
            session = Session.objects.create(
                config=merged_config, user_identifier=user_identifier
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

    def get(self, request, session_id):
        client = request.auth

        try:
            session = Session.objects.get(id=session_id)

            # If client is authenticated, verify ownership
            if client and session.client != client:
                return Response(
                    {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
                )

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

    def put(self, request, session_id):
        client = request.auth

        try:
            session = Session.objects.get(id=session_id)

            # If client is authenticated, verify ownership
            if client and session.client != client:
                return Response(
                    {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
                )

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

    def get(self, request):
        from datetime import timedelta

        client = request.auth

        # If client is authenticated, show only their stats
        if client:
            sessions_query = Session.objects.filter(client=client)
        else:
            sessions_query = Session.objects.all()

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

    def get(self, request):
        from django.db.models import Count

        client = request.auth

        # If client is authenticated, show only their stats
        if client:
            sessions_query = Session.objects.filter(client=client)
        else:
            sessions_query = Session.objects.all()

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
