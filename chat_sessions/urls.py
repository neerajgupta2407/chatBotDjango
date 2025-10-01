from django.urls import path

from . import views

urlpatterns = [
    path("create", views.SessionCreateView.as_view(), name="session-create"),
    path("<uuid:session_id>", views.SessionDetailView.as_view(), name="session-detail"),
    path(
        "<uuid:session_id>/config",
        views.SessionConfigUpdateView.as_view(),
        name="session-config-update",
    ),
    path("stats/summary", views.SessionStatsView.as_view(), name="session-stats"),
    path("bot-config", views.BotConfigView.as_view(), name="bot-config"),
]
