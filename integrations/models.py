"""
API keys and third-party integration models.
"""

import secrets
import uuid

from django.db import models


class APIKey(models.Model):
    """API keys for programmatic access"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "users.Organization", on_delete=models.CASCADE, related_name="api_keys"
    )

    name = models.CharField(max_length=255)
    key = models.CharField(max_length=255, unique=True, editable=False)
    key_prefix = models.CharField(max_length=20)  # First 8 chars for display

    # Permissions (using JSONField for SQLite compatibility)
    scopes = models.JSONField(default=list)

    # Rate limiting
    rate_limit_per_minute = models.IntegerField(default=60)

    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey("users.User", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "api_keys"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.key_prefix}...)"

    def save(self, *args, **kwargs):
        """Auto-generate API key"""
        if not self.key:
            self.key = f"sk_{secrets.token_urlsafe(48)}"
            self.key_prefix = self.key[:12]
        super().save(*args, **kwargs)


class Integration(models.Model):
    """Third-party integrations (Slack, Teams, etc.)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "users.Organization", on_delete=models.CASCADE, related_name="integrations"
    )

    integration_type = models.CharField(
        max_length=50,
        choices=[
            ("slack", "Slack"),
            ("teams", "Microsoft Teams"),
            ("gmail", "Gmail"),
            ("chrome", "Chrome Extension"),
        ],
    )

    config = models.JSONField(default=dict)
    credentials = models.JSONField(default=dict)  # Should be encrypted in production

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "integrations"
        ordering = ["integration_type"]

    def __str__(self):
        return f"{self.get_integration_type_display()} ({self.organization.name})"
