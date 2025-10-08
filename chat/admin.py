from django.contrib import admin
from django.utils.html import format_html

from .models import FileUpload, Message, Session


class MessageInline(admin.TabularInline):
    """Inline for displaying messages within a session"""

    model = Message
    extra = 0
    readonly_fields = ("content_preview", "timestamp")
    fields = ("role", "content_preview", "timestamp")
    can_delete = True

    def content_preview(self, obj):
        """Show preview of message content"""
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content

    content_preview.short_description = "Content"


class FileUploadInline(admin.TabularInline):
    """Inline for displaying uploaded files within a session"""

    model = FileUpload
    extra = 0
    readonly_fields = ("uploaded_at", "file_size_display")
    fields = (
        "original_name",
        "file_type",
        "file_size_display",
        "is_active",
        "uploaded_at",
    )
    can_delete = True

    def file_size_display(self, obj):
        """Display file size in human-readable format"""
        if obj.file_size is None:
            return "-"
        size = obj.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

    file_size_display.short_description = "File Size"


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "client_link",
        "user_identifier",
        "message_count",
        "file_count",
        "is_expired",
        "created_at",
        "last_activity",
    )
    list_filter = ("client", "user_identifier", "created_at", "last_activity")
    search_fields = ("id", "client__name", "client__email", "user_identifier")
    readonly_fields = ("id", "created_at", "last_activity", "is_expired_display")
    inlines = [MessageInline, FileUploadInline]

    fieldsets = (
        (
            "Session Info",
            {
                "fields": (
                    "id",
                    "client",
                    "user_identifier",
                    "is_expired_display",
                )
            },
        ),
        (
            "Configuration",
            {
                "fields": ("config",),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "last_activity"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["delete_expired_sessions"]

    def client_link(self, obj):
        """Display client with link if available"""
        if obj.client:
            return format_html(
                '<a href="/admin/clients/client/{}/change/">{}</a>',
                obj.client.id,
                obj.client.name,
            )
        return "-"

    client_link.short_description = "Client"

    def message_count(self, obj):
        """Count of messages in session"""
        return obj.conversation_messages.count()

    message_count.short_description = "Messages"

    def file_count(self, obj):
        """Count of uploaded files in session"""
        return obj.uploaded_files.filter(is_active=True).count()

    file_count.short_description = "Files"

    def is_expired_display(self, obj):
        """Display if session is expired"""
        expired = obj.is_expired()
        color = "red" if expired else "green"
        text = "Yes" if expired else "No"
        return format_html('<span style="color: {};">{}</span>', color, text)

    is_expired_display.short_description = "Expired"

    def delete_expired_sessions(self, request, queryset):
        """Delete expired sessions"""
        expired = [session for session in queryset if session.is_expired()]
        count = len(expired)
        for session in expired:
            session.delete()
        self.message_user(request, f"Deleted {count} expired session(s)")

    delete_expired_sessions.short_description = "Delete expired sessions"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "session_link",
        "role",
        "content_preview",
        "timestamp",
    )
    list_filter = ("role", "timestamp")
    search_fields = ("content", "session__id")
    readonly_fields = ("timestamp",)

    fieldsets = (
        (
            "Message Info",
            {
                "fields": (
                    "session",
                    "role",
                    "content",
                    "timestamp",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": ("metadata",),
                "classes": ("collapse",),
            },
        ),
    )

    def session_link(self, obj):
        """Display session with link"""
        return format_html(
            '<a href="/admin/chat/session/{}/change/">{}</a>',
            obj.session.id,
            str(obj.session.id)[:8],
        )

    session_link.short_description = "Session"

    def content_preview(self, obj):
        """Show preview of message content"""
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content

    content_preview.short_description = "Content"


@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "session_link",
        "original_name",
        "file_type",
        "file_size_display",
        "is_active",
        "uploaded_at",
    )
    list_filter = ("file_type", "is_active", "uploaded_at")
    search_fields = ("original_name", "session__id")
    readonly_fields = ("uploaded_at", "file_size_display")

    fieldsets = (
        (
            "File Info",
            {
                "fields": (
                    "session",
                    "original_name",
                    "file_path",
                    "file_type",
                    "file_size_display",
                    "is_active",
                )
            },
        ),
        (
            "Processed Data",
            {
                "fields": (
                    "processed_data",
                    "summary",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("uploaded_at",),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["mark_as_active", "mark_as_inactive"]

    def session_link(self, obj):
        """Display session with link"""
        return format_html(
            '<a href="/admin/chat/session/{}/change/">{}</a>',
            obj.session.id,
            str(obj.session.id)[:8],
        )

    session_link.short_description = "Session"

    def file_size_display(self, obj):
        """Display file size in human-readable format"""
        if obj.file_size is None:
            return "-"
        size = obj.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

    file_size_display.short_description = "File Size"

    def mark_as_active(self, request, queryset):
        """Mark selected files as active"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Marked {updated} file(s) as active")

    mark_as_active.short_description = "Mark as active"

    def mark_as_inactive(self, request, queryset):
        """Mark selected files as inactive"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Marked {updated} file(s) as inactive")

    mark_as_inactive.short_description = "Mark as inactive"
