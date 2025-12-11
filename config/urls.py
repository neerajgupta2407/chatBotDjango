"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.utils import timezone
from django.views.generic import TemplateView

from clients.views import WidgetConfigView, WidgetHTMLView, WidgetJavaScriptView


def health_check(request):
    """Health check endpoint"""
    return JsonResponse({"status": "OK", "timestamp": timezone.now().isoformat()})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health", health_check, name="health-check"),
    path("api/chat/", include("chat.urls")),
    path("api/clients/", include("clients.urls")),
    path("api/widget/config", WidgetConfigView.as_view(), name="widget-config"),
    # Widget files (served dynamically with client config)
    path("widget/chatbot.js", WidgetJavaScriptView.as_view(), name="widget-js"),
    path("widget/chatbot.html", WidgetHTMLView.as_view(), name="widget-html"),
    # Demo page
    path("demo", TemplateView.as_view(template_name="demo.html"), name="demo"),
    # Test pages
    path(
        "test-debounce",
        TemplateView.as_view(template_name="test-debounce.html"),
        name="test-debounce",
    ),
    path(
        "test-widget",
        TemplateView.as_view(template_name="test-widget.html"),
        name="test-widget",
    ),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.BASE_DIR / "static"
    )
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
