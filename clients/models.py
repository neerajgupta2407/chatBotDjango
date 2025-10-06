import secrets
import uuid

from django.db import models


class Client(models.Model):
    """
    Represents a tenant/customer in the multi-tenant chatbot system.
    Each client has a unique API key for authentication and custom configuration.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    api_key = models.CharField(
        max_length=64, unique=True, db_index=True, editable=False
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["api_key"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate API key on creation"""
        if not self.api_key:
            self.api_key = self.generate_api_key()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_api_key():
        """Generate secure API key with cb_ prefix"""
        return f"cb_{secrets.token_urlsafe(48)}"

    def regenerate_api_key(self):
        """Regenerate API key for this client"""
        self.api_key = self.generate_api_key()
        self.save(update_fields=["api_key", "updated_at"])
        return self.api_key
