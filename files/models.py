"""
File storage and management models.
"""

import uuid

from django.db import models


class File(models.Model):
    """Enhanced file storage for sessions and organization"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        "chat.Session",
        on_delete=models.CASCADE,
        related_name="files",
        null=True,
        blank=True,
    )
    organization = models.ForeignKey(
        "users.Organization", on_delete=models.CASCADE, related_name="files"
    )

    # File info
    filename = models.CharField(max_length=500)
    file_type = models.CharField(max_length=100)
    file_path = models.CharField(max_length=1000)
    file_size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100)

    # Processing
    status = models.CharField(
        max_length=20,
        choices=[
            ("uploaded", "Uploaded"),
            ("processing", "Processing"),
            ("ready", "Ready"),
            ("failed", "Failed"),
        ],
        default="uploaded",
    )

    # Extracted data
    extracted_text = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)

    # For CSV/JSON analysis
    data_summary = models.JSONField(null=True, blank=True)

    uploaded_by = models.ForeignKey("users.User", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "files"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["session", "created_at"]),
            models.Index(fields=["organization", "created_at"]),
        ]

    def __str__(self):
        return f"{self.filename} ({self.file_type})"
