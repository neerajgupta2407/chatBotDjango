from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Session


class SessionCreateView(APIView):
    """Create a new session"""

    def post(self, request):
        config = request.data.get("config", {})

        # Merge environment-based bot configuration with user config
        bot_config = {
            "botName": settings.BOT_NAME,
            "poweredBy": settings.BOT_POWERED_BY,
            "botColor": settings.BOT_COLOR,
            "botIcon": settings.BOT_ICON,
            "botMsgBgColor": settings.BOT_MSG_BG_COLOR,
        }

        merged_config = {**bot_config, **config}

        session = Session.objects.create(config=merged_config)

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
        try:
            session = Session.objects.get(id=session_id)
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
        try:
            session = Session.objects.get(id=session_id)
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

        total_sessions = Session.objects.count()
        five_minutes_ago = timezone.now() - timedelta(minutes=5)
        recently_active = Session.objects.filter(
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
