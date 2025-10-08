"""
Unified URL configuration for chat app
Combines URLs from sessions, messages, and files
"""

from django.urls import path

from chat import views

urlpatterns = [
    # Session endpoints (from chatbot_sessions)
    path("sessions/create", views.SessionCreateView.as_view(), name="session-create"),
    path(
        "sessions/<uuid:session_id>",
        views.SessionDetailView.as_view(),
        name="session-detail",
    ),
    path(
        "sessions/<uuid:session_id>/config",
        views.SessionConfigUpdateView.as_view(),
        name="session-config-update",
    ),
    path(
        "sessions/stats/summary",
        views.SessionStatsView.as_view(),
        name="session-stats",
    ),
    path("sessions/bot-config", views.BotConfigView.as_view(), name="bot-config"),
    # Message endpoints (from conversations)
    path("messages/send", views.ChatMessageView.as_view(), name="chat-message"),
    path(
        "messages/history/<uuid:session_id>",
        views.ChatHistoryView.as_view(),
        name="chat-history",
    ),
    path(
        "messages/clear/<uuid:session_id>",
        views.ClearHistoryView.as_view(),
        name="chat-clear-history",
    ),
    # File endpoints (from files)
    path("files/upload", views.FileUploadView.as_view(), name="file-upload"),
    path(
        "files/info/<uuid:session_id>",
        views.FileInfoView.as_view(),
        name="file-info",
    ),
    path(
        "files/query/<uuid:session_id>",
        views.FileQueryView.as_view(),
        name="file-query",
    ),
    path(
        "files/<uuid:session_id>",
        views.FileDeleteView.as_view(),
        name="file-delete",
    ),
]
