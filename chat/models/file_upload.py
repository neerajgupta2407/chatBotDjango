from django.db import models
from django.utils import timezone


class FileUpload(models.Model):
    """
    Uploaded file associated with a session.
    Extracted from Session.file_data JSONField for proper data normalization.
    """

    FILE_TYPE_CHOICES = [
        ("json", "JSON"),
        ("csv", "CSV"),
    ]

    session = models.ForeignKey(
        "Session",
        on_delete=models.CASCADE,
        related_name="uploaded_files",
    )

    # File information
    original_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    file_size = models.IntegerField(help_text="File size in bytes")

    # Processed data
    processed_data = models.JSONField(
        default=dict, blank=True, help_text="Parsed and processed file data"
    )
    summary = models.TextField(blank=True, help_text="AI-generated summary of file")

    # Metadata
    uploaded_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(
        default=True, help_text="False if file has been deleted"
    )

    class Meta:
        db_table = "file_uploads"
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["session", "-uploaded_at"]),
            models.Index(fields=["session", "is_active"]),
        ]

    def __str__(self):
        return f"{self.original_name} ({self.file_type})"

    def to_dict(self):
        """Convert to dictionary format (compatible with old JSON structure)"""
        return {
            "originalName": self.original_name,
            "uploadedAt": int(self.uploaded_at.timestamp() * 1000),
            "filePath": self.file_path,
            "type": self.file_type,
            "size": self.file_size,
            "summary": self.summary,
            **self.processed_data,
        }
