from django.db import models
from django.utils import timezone


class Message(models.Model):
    """
    Individual message in a conversation session.
    Extracted from Session.messages JSONField for proper data normalization.
    """

    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    ]

    session = models.ForeignKey(
        "Session",
        on_delete=models.CASCADE,
        related_name="conversation_messages",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    # Optional metadata
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "conversation_messages"
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["session", "timestamp"]),
            models.Index(fields=["session", "-timestamp"]),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."

    def to_dict(self):
        """Convert to dictionary format (compatible with old JSON structure)"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": int(self.timestamp.timestamp() * 1000),
            **self.metadata,
        }
