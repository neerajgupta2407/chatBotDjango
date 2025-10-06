from django.urls import path

from . import views

urlpatterns = [
    path("me/config", views.ClientConfigView.as_view(), name="client-config"),
    path(
        "me/regenerate-key",
        views.RegenerateAPIKeyView.as_view(),
        name="regenerate-api-key",
    ),
    path(
        "me/widget-code", views.WidgetEmbedCodeView.as_view(), name="widget-embed-code"
    ),
]
