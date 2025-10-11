import uuid

from django.db import models
from django.utils import timezone


class Message(models.Model):
    """
    Enhanced message model with cost tracking, RAG sources, and edit history.
    Individual message in a conversation session.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

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

    # Edit history
    is_edited = models.BooleanField(default=False)
    original_content = models.TextField(blank=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    # AI Metadata
    provider_name = models.CharField(max_length=50, blank=True)
    model = models.CharField(max_length=100, blank=True)

    # Tokens & cost tracking
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)

    # Attachments
    attachments = models.JSONField(default=list, blank=True)

    # RAG context - knowledge base sources used for this response
    kb_sources = models.JSONField(
        default=list,
        blank=True,
        help_text="Knowledge base sources used for generating this response",
    )

    # Timestamps
    timestamp = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional metadata (maintain backward compatibility)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "conversation_messages"
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["session", "timestamp"]),
            models.Index(fields=["session", "-timestamp"]),
            models.Index(fields=["session", "role"]),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."

    def to_dict(self):
        """Convert to dictionary format (compatible with old JSON structure)"""
        result = {
            "id": str(self.id),
            "role": self.role,
            "content": self.content,
            "timestamp": int(self.timestamp.timestamp() * 1000),
            **self.metadata,
        }

        # Add cost and token info for assistant messages
        if self.role == "assistant":
            result.update(
                {
                    "provider": self.provider_name,
                    "model": self.model,
                    "tokens": {
                        "prompt": self.prompt_tokens,
                        "completion": self.completion_tokens,
                        "total": self.total_tokens,
                    },
                    "cost": float(self.cost),
                    "kb_sources": self.kb_sources,
                }
            )

        return result
