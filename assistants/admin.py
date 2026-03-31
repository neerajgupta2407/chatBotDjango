"""
Admin configuration for assistants app.
"""

from django.contrib import admin

from .models import AIModel, Assistant


@admin.register(Assistant)
class AssistantAdmin(admin.ModelAdmin):
    """Admin interface for Assistant model"""

    list_display = [
        "name",
        "organization",
        "provider",
        "model",
        "is_active",
        "is_default",
        "created_at",
    ]
    list_filter = ["provider", "is_active", "is_default", "organization"]
    search_fields = ["name", "description", "display_name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    filter_horizontal = ["knowledge_collections"]


@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    """Admin interface for AIModel model"""

    list_display = [
        "display_name",
        "provider",
        "model_id",
        "max_context_tokens",
        "input_price",
        "output_price",
        "is_available",
    ]
    list_filter = [
        "provider",
        "is_available",
        "supports_vision",
        "supports_function_calling",
    ]
    search_fields = ["model_id", "display_name"]
    readonly_fields = ["id"]
