"""
Admin configuration for knowledge_base app.
"""

from django.contrib import admin

from .models import Collection, Document, DocumentChunk


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    """Admin interface for Collection model"""

    list_display = ["name", "organization", "is_public", "created_by", "created_at"]
    list_filter = ["is_public", "organization", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Document model"""

    list_display = [
        "title",
        "collection",
        "file_type",
        "status",
        "source_type",
        "created_at",
    ]
    list_filter = ["status", "source_type", "file_type", "collection"]
    search_fields = ["title", "content"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    """Admin interface for DocumentChunk model"""

    list_display = ["document", "chunk_index", "tokens"]
    list_filter = ["document"]
    search_fields = ["content"]
    readonly_fields = ["id"]
