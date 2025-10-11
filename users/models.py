"""
User and Organization models for multi-tenant chatbot platform.
"""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify


class Organization(models.Model):
    """
    Organization/Tenant model for multi-tenant support.
    Each organization has its own assistants, knowledge base, and users.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    # Subscription & limits
    plan = models.CharField(
        max_length=50,
        default="free",
        choices=[
            ("free", "Free"),
            ("starter", "Starter"),
            ("professional", "Professional"),
            ("enterprise", "Enterprise"),
        ],
    )
    monthly_token_limit = models.IntegerField(default=100000)
    monthly_tokens_used = models.IntegerField(default=0)

    class Meta:
        db_table = "organizations"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug if not provided"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Each user belongs to an organization and has a role.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="users"
    )
    role = models.CharField(
        max_length=20,
        choices=[
            ("admin", "Admin"),
            ("member", "Member"),
            ("viewer", "Viewer"),
        ],
        default="member",
    )

    # Fix for groups and user_permissions clash
    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name="groups",
        blank=True,
        help_text="The groups this user belongs to.",
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name="user permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        related_name="custom_user_set",
        related_query_name="custom_user",
    )

    class Meta:
        db_table = "users"
        ordering = ["email"]
        indexes = [
            models.Index(fields=["organization", "role"]),
        ]

    def __str__(self):
        return f"{self.email} ({self.organization.name})"
