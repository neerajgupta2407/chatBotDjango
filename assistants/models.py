"""
Assistant and AI Model configuration models.
"""

import uuid

from django.db import models


class Assistant(models.Model):
    """
    AI Assistant configuration with custom instructions and knowledge base.
    Each organization can create multiple assistants with different capabilities.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "users.Organization", on_delete=models.CASCADE, related_name="assistants"
    )

    # Basic info
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    display_name = models.CharField(max_length=255)
    icon_url = models.URLField(blank=True)

    # AI Configuration
    provider = models.CharField(
        max_length=50,
        choices=[
            ("claude", "Anthropic Claude"),
            ("openai", "OpenAI GPT"),
            ("gemini", "Google Gemini"),
        ],
    )
    model = models.CharField(max_length=100)  # e.g., 'gpt-4', 'claude-3-opus'

    # Behavior
    system_instructions = models.TextField(help_text="System prompt for the assistant")
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=2000)

    # Features
    supports_vision = models.BooleanField(default=False)
    supports_function_calling = models.BooleanField(default=False)
    supports_file_analysis = models.BooleanField(default=True)

    # Knowledge base
    knowledge_collections = models.ManyToManyField(
        "knowledge_base.Collection", blank=True, related_name="assistants"
    )

    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "assistants"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["organization", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class AIModel(models.Model):
    """
    Available AI models and their capabilities.
    Centralized model configuration for pricing and features.
    """

    id = models.AutoField(primary_key=True)
    provider = models.CharField(max_length=50)
    model_id = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)

    # Capabilities
    supports_vision = models.BooleanField(default=False)
    supports_function_calling = models.BooleanField(default=False)
    max_context_tokens = models.IntegerField()
    max_output_tokens = models.IntegerField()

    # Pricing (per 1M tokens)
    input_price = models.DecimalField(max_digits=10, decimal_places=4)
    output_price = models.DecimalField(max_digits=10, decimal_places=4)

    is_available = models.BooleanField(default=True)

    class Meta:
        db_table = "ai_models"
        ordering = ["provider", "model_id"]

    def __str__(self):
        return f"{self.display_name} ({self.provider})"
