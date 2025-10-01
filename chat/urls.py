from django.urls import path

from . import views

urlpatterns = [
    path("message", views.ChatMessageView.as_view(), name="chat-message"),
    path(
        "history/<uuid:session_id>",
        views.ChatHistoryView.as_view(),
        name="chat-history",
    ),
    path(
        "history/<uuid:session_id>",
        views.ClearHistoryView.as_view(),
        name="chat-clear-history",
    ),
]
