"""
Prompt template library models.
"""

import uuid

from django.db import models


class PromptTemplate(models.Model):
    """Reusable prompt templates with variables"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "users.Organization", on_delete=models.CASCADE, related_name="prompts"
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100)

    # Template content
    template = models.TextField(help_text="Prompt with {{variable}} placeholders")
    variables = models.JSONField(
        default=list, help_text="List of variable names and descriptions"
    )

    # Sharing
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey("users.User", on_delete=models.CASCADE)

    # Usage tracking
    use_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "prompt_templates"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.category})"
