"""
Knowledge Base models with vector embeddings for semantic search.
Requires PostgreSQL with pgvector extension.
"""

import uuid

from django.db import models

# Conditional import for pgvector - only available with PostgreSQL
try:
    from pgvector.django import VectorField

    def get_vector_field():
        return VectorField(dimensions=1536)

except ImportError:
    # Fallback for testing with SQLite
    VectorField = None

    def get_vector_field():
        return models.BinaryField(null=True, blank=True)


class Collection(models.Model):
    """
    Knowledge base collection grouping related documents.
    Can be attached to multiple assistants.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "users.Organization", on_delete=models.CASCADE, related_name="collections"
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Access control
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey("users.User", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "kb_collections"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["organization", "is_public"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class Document(models.Model):
    """
    Document within a knowledge base collection.
    Stores original file and processed content.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, related_name="documents"
    )

    # File info
    title = models.CharField(max_length=500)
    file_type = models.CharField(max_length=50)
    file_path = models.CharField(max_length=1000)
    file_size = models.BigIntegerField()

    # Content
    content = models.TextField()
    metadata = models.JSONField(default=dict)

    # Processing status
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending",
    )

    # Source tracking
    source_url = models.URLField(blank=True)
    source_type = models.CharField(
        max_length=50,
        choices=[
            ("upload", "Upload"),
            ("confluence", "Confluence"),
            ("notion", "Notion"),
            ("sharepoint", "SharePoint"),
            ("web", "Web Scrape"),
        ],
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "kb_documents"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["collection", "status"]),
        ]

    def __str__(self):
        return self.title


class DocumentChunk(models.Model):
    """
    Chunked document content for RAG (Retrieval-Augmented Generation).
    Each chunk has a vector embedding for semantic search.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="chunks"
    )

    content = models.TextField()
    chunk_index = models.IntegerField()

    # Vector embedding (1536 dimensions for OpenAI ada-002)
    # This enables semantic search using cosine similarity
    # Use BinaryField as fallback when VectorField is not available (testing)
    embedding = get_vector_field()

    # Metadata
    tokens = models.IntegerField()
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = "kb_chunks"
        ordering = ["document", "chunk_index"]
        indexes = [
            models.Index(fields=["document", "chunk_index"]),
        ]

    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"
