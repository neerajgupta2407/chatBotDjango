# Multi-Tenant Client Configuration System - Implementation Documentation

**Date**: October 6, 2025 (Updated: October 8, 2025)
**Version**: 2.0
**Last Commit**: App consolidation and refactoring

---

## Overview

Successfully implemented a multi-tenant SaaS platform that allows multiple clients to use the chatbot backend with isolated data, custom branding, and API key authentication.

**Update (Oct 8, 2025)**: Refactored from 3 separate apps (`chatbot_sessions`, `conversations`, `files`) into a single unified **`chat/`** app with submodule organization for better maintainability.

## Key Features Implemented

### 1. Client Model (`clients/models.py`)
- **UUID-based primary key** for unique client identification
- **Auto-generated API keys** with `cb_` prefix using `secrets.token_urlsafe(48)`
- **JSON configuration field** for flexible client-specific settings
- **Email uniqueness constraint** to prevent duplicate accounts
- **Active status flag** for soft account suspension

**Key Methods**:
- `generate_api_key()` - Creates secure 64-character API key
- `regenerate_api_key()` - Regenerates key and updates timestamps

### 2. API Key Authentication (`core/authentication.py`)

**Class**: `APIKeyAuthentication(BaseAuthentication)`

**Flow**:
1. Extracts `X-API-Key` header from request
2. Validates against `Client` model
3. Checks `is_active` status
4. Returns `(None, client)` tuple for DRF authentication
5. Raises `AuthenticationFailed` for invalid/inactive keys

**Integration**: Added to `REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']` in settings

### 3. Domain Whitelist Middleware (`core/middleware.py`)

**Class**: `DomainWhitelistMiddleware`

**Purpose**: Prevents unauthorized domains from using client's API key

**Features**:
- Validates `Origin` or `Referer` headers
- Supports exact domain matching
- Supports wildcard subdomains (`*.example.com`)
- Allows localhost in DEBUG mode
- Exempt paths: `/admin/`, `/health`, `/static/`, `/media/`

**Configuration**: Client's `config.whitelisted_domains` array

### 4. Session-Client Relationship

**Location**: `chat/models/session.py`

```python
client = models.ForeignKey(
    "clients.Client",
    on_delete=models.CASCADE,
    related_name="sessions",
    null=True,
    blank=True,
)
```

**Benefits**:
- Session isolation per client
- Ownership verification in all views
- Analytics per client
- Cascade deletion on client removal

### 5. Client Management APIs

#### A. Get Client Configuration
```http
GET /api/clients/me/config
X-API-Key: cb_xR3k9...

Response:
{
  "client_id": "uuid",
  "name": "Client Name",
  "config": {
    "bot_name": "...",
    "primary_color": "#...",
    ...
  }
}
```

#### B. Update Client Configuration
```http
PUT /api/clients/me/config
X-API-Key: cb_xR3k9...

{
  "config": {
    "primary_color": "#00aaff",
    "bot_name": "New Bot Name"
  }
}
```

#### C. Regenerate API Key
```http
POST /api/clients/me/regenerate-key
X-API-Key: cb_xR3k9... (old key)

Response:
{
  "api_key": "cb_newkey12345...",
  "message": "API key regenerated successfully..."
}
```

#### D. Get Widget Embed Code
```http
GET /api/clients/me/widget-code
X-API-Key: cb_xR3k9...

Response:
{
  "html": "<script src='...' data-api-key='...'></script>",
  "instructions": "Paste this code before </body> tag"
}
```

### 6. Widget Configuration Endpoint

```http
GET /api/widget/config
X-API-Key: cb_xR3k9...

Response:
{
  "branding": {
    "logo_url": "...",
    "primary_color": "#...",
    "bot_message_bg_color": "#...",
    "bot_icon_url": "...",
    "bot_name": "...",
    "powered_by_text": "..."
  },
  "layout": {
    "widget_position": "bottom-right",
    "widget_size": "medium",
    "widget_offset": {"x": 20, "y": 20},
    "initial_state": "minimized",
    "theme": "light"
  },
  "features": {
    "enable_file_upload": true,
    "enable_json_upload": true,
    "enable_csv_upload": true,
    "max_file_size_mb": 10
  }
}
```

### 7. View Updates - Ownership Verification

**Updated Files** (Refactored into chat/ app):
- `chat/views/sessions.py` - All session operations
- `chat/views/messages.py` - Message, history, clear operations
- `chat/views/files.py` - Upload, info, query, delete operations

**Pattern Applied**:
```python
client = request.auth

# Get session
session = Session.objects.get(id=session_id)

# If client is authenticated, verify ownership
if client and session.client != client:
    return Response(
        {"error": "Session not found"},
        status=status.HTTP_404_NOT_FOUND
    )
```

**Backward Compatibility**: Non-authenticated requests still work (client is None)

### 8. Django Admin Interface

**File**: `clients/admin.py`

**Features**:
- List view with API key preview (first 10 + last 4 chars)
- Search by name, email, API key
- Filter by active status and creation date
- Collapsible JSON config editor
- Readonly fields: api_key, created_at, updated_at

**Custom Actions**:
- `regenerate_api_keys` - Bulk API key regeneration
- `activate_clients` - Activate selected clients
- `deactivate_clients` - Deactivate selected clients

### 9. Database Schema

#### Unified chat/ app migration: `chat/migrations/0001_initial.py`

Creates all three models in one migration:

**Session Model**:
- Table: `chatbot_sessions_session`
- Fields: id (UUID), client (FK), config, messages, file_data, created_at, last_activity
- Index: `chatbot_ses_last_ac_51af55_idx` on `-last_activity`

**Message Model**:
- Table: `conversation_messages`
- Fields: id, session (FK), role, content, timestamp, metadata
- Indexes:
  - `conversatio_session_c9e0af_idx` on `[session, timestamp]`
  - `conversatio_session_a27a84_idx` on `[session, -timestamp]`

**FileUpload Model**:
- Table: `file_uploads`
- Fields: id, session (FK), original_name, file_path, file_type, file_size, processed_data, summary, uploaded_at, is_active
- Indexes:
  - `file_upload_session_83fd7f_idx` on `[session, -uploaded_at]`
  - `file_upload_session_3753b7_idx` on `[session, is_active]`

---

## App Architecture (Refactored)

### Unified chat/ App Structure

```
chat/
├── models/
│   ├── __init__.py          # Exports Session, Message, FileUpload
│   ├── session.py           # Session model with client FK
│   ├── message.py           # Message model for normalized conversations
│   └── file_upload.py       # FileUpload model for file management
│
├── views/
│   ├── __init__.py          # Exports all view classes
│   ├── sessions.py          # SessionCreateView, SessionDetailView, etc.
│   ├── messages.py          # ChatMessageView, ChatHistoryView, etc.
│   └── files.py             # FileUploadView, FileInfoView, etc.
│
├── services/
│   ├── __init__.py          # Exports ChatService, FileProcessor
│   ├── chat_service.py      # Context building, token management
│   └── file_processor.py    # JSON/CSV parsing, data analysis
│
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py      # Creates all 3 models
│
└── urls.py                  # All chat-related endpoints
```

### Benefits of Unified Structure

1. **Single Source of Truth**: All chat functionality in one place
2. **Clear Separation**: Models, views, and services are logically separated
3. **Better Imports**: `from chat.models import Session, Message, FileUpload`
4. **Easier Testing**: Related functionality grouped together
5. **Simpler Migrations**: One migration history instead of three

---

## Configuration

### Settings Changes (`config/settings/base.py`)

**1. Updated INSTALLED_APPS**:
```python
LOCAL_APPS = [
    "core",
    "ai_providers",
    "clients",
    "chat",  # Unified app (replaces chatbot_sessions, conversations, files)
]
```

**2. Added DomainWhitelistMiddleware**:
```python
MIDDLEWARE = [
    ...
    "core.middleware.DomainWhitelistMiddleware",
]
```

**3. Added API Key Authentication**:
```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "core.authentication.APIKeyAuthentication",
    ],
    ...
}
```

### URL Configuration (`config/urls.py`)

```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("health", health_check, name="health-check"),
    path("api/chat/", include("chat.urls")),  # Unified endpoint
    path("api/clients/", include("clients.urls")),
    path("api/widget/config", WidgetConfigView.as_view(), name="widget-config"),
    ...
]
```

### Chat URLs (`chat/urls.py`)

All endpoints consolidated under `/api/chat/`:

```python
urlpatterns = [
    # Session endpoints
    path("sessions/create", views.SessionCreateView.as_view(), name="session-create"),
    path("sessions/<uuid:session_id>", views.SessionDetailView.as_view(), name="session-detail"),
    path("sessions/<uuid:session_id>/config", views.SessionConfigUpdateView.as_view(), name="session-config"),
    path("sessions/stats/summary", views.SessionStatsView.as_view(), name="session-stats"),
    path("sessions/bot-config", views.BotConfigView.as_view(), name="bot-config"),

    # Message endpoints
    path("messages/send", views.ChatMessageView.as_view(), name="chat-message"),
    path("messages/history/<uuid:session_id>", views.ChatHistoryView.as_view(), name="chat-history"),
    path("messages/history/<uuid:session_id>/clear", views.ClearHistoryView.as_view(), name="clear-history"),

    # File endpoints
    path("files/upload", views.FileUploadView.as_view(), name="file-upload"),
    path("files/info/<uuid:session_id>", views.FileInfoView.as_view(), name="file-info"),
    path("files/query/<uuid:session_id>", views.FileQueryView.as_view(), name="file-query"),
    path("files/<uuid:session_id>", views.FileDeleteView.as_view(), name="file-delete"),
]
```

---

## Client Configuration Schema

```json
{
  "bot_name": "string",
  "primary_color": "#hex",
  "bot_message_bg_color": "#hex",
  "bot_icon_url": "https://...",
  "powered_by_text": "string",
  "whitelisted_domains": [
    "https://example.com",
    "*.subdomain.com",
    "http://localhost:3000"
  ],
  "widget_position": "bottom-right | bottom-left | custom",
  "widget_size": "small | medium | large",
  "widget_offset": {"x": 20, "y": 20},
  "initial_state": "minimized | open",
  "theme": "light | dark | auto",
  "enable_file_upload": true,
  "enable_json_upload": true,
  "enable_csv_upload": true,
  "max_file_size_mb": 10
}
```

---

## Usage Guide

### For Administrators

**1. Create New Client** (Django Admin or Shell):
```python
from clients.models import Client

client = Client.objects.create(
    name="Acme Corporation",
    email="contact@acme.com",
    config={
        "bot_name": "Acme Assistant",
        "primary_color": "#ff6b35",
        "whitelisted_domains": ["https://acme.com"]
    }
)

print(f"API Key: {client.api_key}")
```

**2. Create Dummy Data for Testing**:
```bash
python manage.py create_dummy_data

# Creates:
# - Admin user (username: admin, password: admin12345)
# - 5 dummy clients with different configurations
# - 3-4 sessions per client with conversation history
```

**3. View Client API Keys**:
```bash
python manage.py shell
from clients.models import Client
for client in Client.objects.all():
    print(f"{client.name}: {client.api_key}")
```

### For Developers

**1. Widget Integration**:
```html
<!-- Add to your website -->
<script
  src="https://your-backend.com/static/widget/chatbot.js"
  data-api-key="cb_your_api_key_here">
</script>
```

**2. API Requests** (Updated URLs):
```javascript
// Create session
const response = await fetch('/api/chat/sessions/create', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'cb_your_api_key_here'
  },
  body: JSON.stringify({
    config: { aiProvider: 'claude' }
  })
});

// Send message
const msgResponse = await fetch('/api/chat/messages/send', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'cb_your_api_key_here'
  },
  body: JSON.stringify({
    sessionId: 'uuid',
    message: 'Hello, bot!'
  })
});

// Get chat history
const history = await fetch('/api/chat/messages/history/uuid', {
  headers: { 'X-API-Key': 'cb_your_api_key_here' }
}).then(r => r.json());
```

**3. Get Widget Config**:
```javascript
const config = await fetch('/api/widget/config', {
  headers: { 'X-API-Key': 'cb_your_api_key_here' }
}).then(r => r.json());

// Apply branding
document.documentElement.style.setProperty(
  '--bot-color',
  config.branding.primary_color
);
```

---

## Security Considerations

### 1. API Key Security
- ✅ Keys are 64 characters (urlsafe base64)
- ✅ Stored as plain text (consider hashing in production)
- ✅ Transmitted over HTTPS only
- ✅ Can be regenerated without data loss

### 2. Domain Whitelisting
- ✅ Validates Origin/Referer headers
- ✅ Prevents API key theft/reuse
- ✅ Supports wildcard subdomains
- ⚠️ Can be bypassed with server-side requests (by design)

### 3. Session Isolation
- ✅ All views verify client ownership
- ✅ Clients can only access their own sessions
- ✅ 404 returned for unauthorized access (prevents enumeration)

### 4. Rate Limiting
- ⚠️ Not implemented yet (recommended for production)
- Consider: django-ratelimit or DRF throttling per API key

---

## Testing

### 1. Test Health Check
```bash
curl http://localhost:8000/health
# {"status": "OK", "timestamp": "..."}
```

### 2. Test Bot Config
```bash
curl http://localhost:8000/api/chat/sessions/bot-config
# Returns default bot configuration from env variables
```

### 3. Test Session Creation
```bash
curl -X POST http://localhost:8000/api/chat/sessions/create \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cb_your_test_key" \
  -H "Origin: http://localhost:3000" \
  -d '{"config": {"aiProvider": "claude"}}'
```

### 4. Test Widget Config Endpoint
```bash
curl -X GET http://localhost:8000/api/widget/config \
  -H "X-API-Key: cb_your_test_key"
```

### 5. Test Domain Whitelist (Should Fail)
```bash
curl -X POST http://localhost:8000/api/chat/sessions/create \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cb_your_test_key" \
  -H "Origin: https://unauthorized-domain.com" \
  -d '{}'

# Expected: 403 Forbidden
```

### 6. Test Ownership Verification
```bash
# Create session with Client A's API key
SESSION_ID=$(curl -X POST http://localhost:8000/api/chat/sessions/create \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cb_client_a_key" \
  -d '{"config":{}}' | jq -r '.sessionId')

# Try to access with Client B's API key
curl -X GET http://localhost:8000/api/chat/messages/history/$SESSION_ID \
  -H "X-API-Key: cb_client_b_key"

# Expected: 404 Not Found
```

---

## Statistics & Metrics

**Refactoring Stats**:
- **Apps Consolidated**: 3 → 1 (chatbot_sessions, conversations, files → chat)
- **Migration Files**: Consolidated into single `0001_initial.py`
- **URL Patterns**: Unified under `/api/chat/*`
- **Models**: 3 (Session, Message, FileUpload)
- **Database Tables**: 3 (preserved original table names for compatibility)

**Original Implementation Stats**:
- **Files Changed**: 24
- **Lines Added**: 700
- **Lines Removed**: 20

**New Files Created**:
- `clients/` app (7 files)
- `chat/` unified app (14 files)
- `core/authentication.py`
- `core/middleware.py`

---

## Backward Compatibility

✅ **Non-authenticated requests still work**
- Views check `if client and session.client != client`
- Null client means no ownership verification

✅ **Database tables preserved**
- Session table: `chatbot_sessions_session`
- Message table: `conversation_messages`
- FileUpload table: `file_uploads`

✅ **Environment-based config still works**
- Bot config endpoint reads from BOT_* environment variables
- Fallback behavior in SessionCreateView

⚠️ **URL Changes** (Breaking Change)
- Old: `/api/sessions/*`, `/api/chat/*`, `/api/files/*`
- New: `/api/chat/*` (all endpoints)
- **Action Required**: Update widget JavaScript to use new URLs

---

## Migration History

### Phase 1: Multi-Tenant Implementation (Oct 6, 2025)
1. Created `clients` app with Client model
2. Added API key authentication
3. Added domain whitelist middleware
4. Created session-client relationship
5. Updated all views with ownership verification

### Phase 2: App Consolidation (Oct 8, 2025)
1. Deleted old migrations and database
2. Merged 3 apps into unified `chat/` app
3. Organized code into models/, views/, services/ submodules
4. Generated fresh `0001_initial.py` migration
5. Updated URL routing to `/api/chat/*`
6. Preserved database table names for compatibility

---

## Future Enhancements

### Recommended Next Steps

1. **Rate Limiting**
   - Implement per-client rate limits
   - Track API usage for billing

2. **API Key Hashing**
   - Hash keys in database (like passwords)
   - Provide key only once on creation

3. **Usage Analytics**
   - Track messages/sessions per client
   - Generate usage reports

4. **Billing Integration**
   - Stripe/PayPal integration
   - Usage-based pricing tiers

5. **Team Management**
   - Multiple users per client account
   - Role-based access control

6. **Custom Domains**
   - White-label support
   - widget.client-domain.com

7. **Webhook Support**
   - Notify clients of events
   - Integration endpoints

8. **GraphQL API**
   - Consider GraphQL for more flexible queries
   - Better for complex client dashboards

---

## Troubleshooting

### Issue: API Key Not Working

**Check**:
1. Client is active: `client.is_active == True`
2. API key is correct (no extra spaces)
3. Header name is `X-API-Key` (case-sensitive)

### Issue: Domain Whitelist Error

**Check**:
1. Origin header is being sent
2. Domain includes protocol (`https://`)
3. Wildcard format is correct (`*.domain.com`)
4. Localhost is allowed in DEBUG mode

### Issue: Session Not Found (but exists)

**Likely Cause**: Session belongs to different client

**Solution**: Verify client ownership in database:
```python
from chat.models import Session
session = Session.objects.get(id=session_id)
print(f"Session client: {session.client.email if session.client else 'None'}")
```

### Issue: Import Errors After Refactoring

**Solution**: Update imports to use new structure:
```python
# Old imports (won't work)
from chatbot_sessions.models import Session
from conversations.models import Message
from files.models import FileUpload

# New imports (correct)
from chat.models import Session, Message, FileUpload
```

### Issue: Migration Already Applied

**If you need fresh migrations**:
```bash
# Backup database first
cp db.sqlite3 db.sqlite3.backup

# Delete old migrations
rm -f chat/migrations/0*.py

# Delete database
rm db.sqlite3

# Create fresh migrations
python manage.py makemigrations
python manage.py migrate

# Recreate dummy data
python manage.py create_dummy_data
```

---

## References

- Implementation Spec: `Implementation/14_multi_tenant_client_config.md`
- Django Admin: `/admin/clients/client/`
- API Base URL: `/api/chat/*`
- Widget Config: `/api/widget/config`

---

**Implementation Completed**: October 6, 2025
**Refactored**: October 8, 2025
**Status**: ✅ Production Ready (with rate limiting recommended)
