from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "api_key_preview", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "email", "api_key")
    readonly_fields = ("api_key", "created_at", "updated_at")

    fieldsets = (
        ("Basic Info", {"fields": ("name", "email", "is_active")}),
        ("Authentication", {"fields": ("api_key",)}),
        (
            "Configuration",
            {"fields": ("config",), "classes": ("collapse",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    actions = ["regenerate_api_keys", "activate_clients", "deactivate_clients"]

    def api_key_preview(self, obj):
        """Show preview of API key (first 10 and last 4 characters)"""
        return f"{obj.api_key[:10]}...{obj.api_key[-4:]}"

    api_key_preview.short_description = "API Key"

    def regenerate_api_keys(self, request, queryset):
        """Regenerate API keys for selected clients"""
        count = 0
        for client in queryset:
            old_key = client.api_key
            client.regenerate_api_key()
            count += 1
            self.message_user(
                request, f"Regenerated API key for {client.name}: {client.api_key}"
            )

        self.message_user(request, f"Regenerated {count} API key(s)")

    regenerate_api_keys.short_description = "Regenerate API keys"

    def activate_clients(self, request, queryset):
        """Activate selected clients"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} client(s)")

    activate_clients.short_description = "Activate selected clients"

    def deactivate_clients(self, request, queryset):
        """Deactivate selected clients"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {updated} client(s)")

    deactivate_clients.short_description = "Deactivate selected clients"
