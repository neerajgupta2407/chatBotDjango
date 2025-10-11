"""
Admin configuration for users app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Organization, User


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin interface for Organization model"""

    list_display = ["name", "slug", "plan", "monthly_tokens_used", "created_at"]
    list_filter = ["plan", "created_at"]
    search_fields = ["name", "slug"]
    readonly_fields = ["id", "created_at"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for custom User model"""

    list_display = [
        "email",
        "username",
        "organization",
        "role",
        "is_active",
        "is_staff",
    ]
    list_filter = ["role", "is_active", "is_staff", "organization"]
    search_fields = ["email", "username", "first_name", "last_name"]
    readonly_fields = ["id", "date_joined", "last_login"]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Organization", {"fields": ("organization", "role")}),
    )
