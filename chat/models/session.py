import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Session(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="sessions",
        null=True,
        blank=True,
    )
    config = models.JSONField(default=dict, blank=True)
    messages = models.JSONField(default=list, blank=True)
    file_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chatbot_sessions_session"
        ordering = ["-last_activity"]
        indexes = [
            models.Index(fields=["-last_activity"]),
        ]

    def __str__(self):
        return str(self.id)

    def is_expired(self):
        """Check if session has expired based on CHAT_SESSION_TIMEOUT setting"""
        timeout = timedelta(seconds=settings.CHAT_SESSION_TIMEOUT)
        return timezone.now() - self.last_activity > timeout

    def update_activity(self):
        """Update last_activity timestamp"""
        self.last_activity = timezone.now()
        self.save(update_fields=["last_activity"])
