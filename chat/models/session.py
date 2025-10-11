import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Session(models.Model):
    """
    Enhanced Session model with organization support and analytics.
    Maintains backward compatibility with existing client-based system.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Legacy client field (maintain backward compatibility)
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="sessions",
        null=True,
        blank=True,
    )

    # New organization-based multi-tenancy
    organization = models.ForeignKey(
        "users.Organization",
        on_delete=models.CASCADE,
        related_name="sessions",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_sessions",
    )

    # Chat metadata
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    tags = models.JSONField(
        default=list, blank=True
    )  # Using JSONField for SQLite compatibility

    # Assistant reference
    assistant = models.ForeignKey(
        "assistants.Assistant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # User tracking
    user_identifier = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )

    # Legacy config (maintain backward compatibility)
    config = models.JSONField(default=dict, blank=True)

    # Status
    archived = models.BooleanField(default=False)
    is_shared = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    # Analytics
    total_tokens = models.IntegerField(default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    message_count = models.IntegerField(default=0)

    class Meta:
        db_table = "chatbot_sessions_session"
        ordering = ["-last_activity"]
        indexes = [
            models.Index(fields=["-last_activity"]),
            models.Index(fields=["organization", "-last_activity"]),
            models.Index(fields=["created_by", "-created_at"]),
            models.Index(fields=["archived", "-last_activity"]),
        ]

    def __str__(self):
        if self.title:
            return f"{self.title} ({self.id})"
        return str(self.id)

    def is_expired(self):
        """Check if session has expired based on CHAT_SESSION_TIMEOUT setting"""
        timeout = timedelta(seconds=settings.CHAT_SESSION_TIMEOUT)
        return timezone.now() - self.last_activity > timeout

    def update_activity(self):
        """Update last_activity timestamp"""
        self.last_activity = timezone.now()
        self.save(update_fields=["last_activity"])
