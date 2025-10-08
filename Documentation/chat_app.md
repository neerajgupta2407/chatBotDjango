# Chat App - Complete Documentation

**Version**: 2.0
**Date**: October 8, 2025
**Status**: Production Ready

---

## Overview

The `chat/` app is a unified Django application that handles all chat-related functionality including sessions, messages, and file uploads. It provides a complete conversational AI interface with normalized database storage, multi-provider support, and file analysis capabilities.

### Key Features

- **Session Management**: Create and manage chat sessions with custom configurations
- **Message Storage**: Normalized database storage for all conversation messages
- **AI Provider Integration**: Support for Claude, OpenAI, and custom providers
- **File Upload & Analysis**: JSON/CSV file upload with AI-powered analysis
- **Multi-Tenant Support**: Client isolation with API key authentication
- **Context Building**: Smart context management with token limits
- **Message History**: Full conversation history with chronological ordering

---

## App Architecture

### Directory Structure

```
chat/
├── __init__.py
├── apps.py
│
├── models/
│   ├── __init__.py          # Exports: Session, Message, FileUpload
│   ├── session.py           # Session model with config and metadata
│   ├── message.py           # Normalized message storage
│   └── file_upload.py       # File upload metadata and processing
│
├── views/
│   ├── __init__.py          # Exports all view classes
│   ├── sessions.py          # Session CRUD operations
│   ├── messages.py          # Message send/retrieve/clear operations
│   └── files.py             # File upload and query operations
│
├── services/
│   ├── __init__.py          # Exports: ChatService, FileProcessor
│   ├── chat_service.py      # Context building and token management
│   └── file_processor.py    # JSON/CSV parsing and analysis
│
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py      # Creates all 3 models
│
└── urls.py                  # All API endpoints
```

---

## Models

### 1. Session Model (`chat/models/session.py`)

Represents a chat session with configuration and state.

**Fields:**
- `id` (UUID): Primary key, auto-generated
- `client` (FK): Foreign key to Client model (nullable for backward compatibility)
- `config` (JSONField): Session configuration (AI provider, page context, etc.)
- `messages` (JSONField): Legacy field, no longer used
- `file_data` (JSONField): Legacy field for file data
- `created_at` (DateTime): Auto-set on creation
- `last_activity` (DateTime): Auto-updated on save

**Database Table**: `chatbot_sessions_session`

**Indexes:**
- `chatbot_ses_last_ac_51af55_idx` on `-last_activity`

**Related Names:**
- `conversation_messages`: Related Message objects
- `uploaded_files`: Related FileUpload objects

**Methods:**
```python
def is_expired() -> bool:
    """Check if session has expired based on CHAT_SESSION_TIMEOUT"""

def update_activity():
    """Update last_activity timestamp"""
```

**Example:**
```python
from chat.models import Session

# Create session
session = Session.objects.create(
    config={
        "aiProvider": "claude",
        "pageContext": {
            "url": "https://example.com",
            "title": "Example Page"
        }
    }
)

# Check expiration
if session.is_expired():
    print("Session has expired")

# Get messages
messages = session.conversation_messages.all()
```

---

### 2. Message Model (`chat/models/message.py`)

Stores individual messages in normalized format.

**Fields:**
- `id` (BigInt): Auto-increment primary key
- `session` (FK): Foreign key to Session
- `role` (CharField): Message role - choices: 'user', 'assistant', 'system'
- `content` (TextField): Message text content
- `timestamp` (DateTime): Auto-set on creation
- `metadata` (JSONField): Additional data (provider, model, etc.)

**Database Table**: `conversation_messages`

**Indexes:**
- `conversatio_session_c9e0af_idx` on `[session, timestamp]`
- `conversatio_session_a27a84_idx` on `[session, -timestamp]`

**Methods:**
```python
def to_dict() -> dict:
    """Convert to dictionary format for API responses"""
    return {
        "role": self.role,
        "content": self.content,
        "timestamp": int(self.timestamp.timestamp() * 1000),
        **self.metadata
    }
```

**Example:**
```python
from chat.models import Message, Session

session = Session.objects.get(id="uuid")

# Create user message
msg = Message.objects.create(
    session=session,
    role="user",
    content="What is Python?"
)

# Create assistant message with metadata
assistant_msg = Message.objects.create(
    session=session,
    role="assistant",
    content="Python is a programming language...",
    metadata={
        "provider": "claude",
        "model": "claude-3-5-haiku-20241022"
    }
)

# Query messages
recent_messages = Message.objects.filter(
    session=session
).order_by('-timestamp')[:10]
```

---

### 3. FileUpload Model (`chat/models/file_upload.py`)

Stores uploaded file metadata and processed data.

**Fields:**
- `id` (BigInt): Auto-increment primary key
- `session` (FK): Foreign key to Session
- `original_name` (CharField): Original filename
- `file_path` (CharField): Path to stored file
- `file_type` (CharField): File type - choices: 'json', 'csv'
- `file_size` (Int): File size in bytes
- `processed_data` (JSONField): Parsed and processed file data
- `summary` (TextField): AI-generated summary
- `uploaded_at` (DateTime): Auto-set on creation
- `is_active` (Boolean): Soft delete flag

**Database Table**: `file_uploads`

**Indexes:**
- `file_upload_session_83fd7f_idx` on `[session, -uploaded_at]`
- `file_upload_session_3753b7_idx` on `[session, is_active]`

**Methods:**
```python
def to_dict() -> dict:
    """Convert to dictionary format compatible with old JSON structure"""
```

**Example:**
```python
from chat.models import FileUpload

# Create file upload
file_upload = FileUpload.objects.create(
    session=session,
    original_name="data.csv",
    file_path="/media/uploads/data.csv",
    file_type="csv",
    file_size=1024,
    processed_data={"columns": ["id", "name"], "rows": 100},
    summary="Customer data with 100 records"
)

# Query active files
active_files = FileUpload.objects.filter(
    session=session,
    is_active=True
)
```

---

## API Endpoints

### Base URL
All endpoints are under `/api/chat/`

### Session Endpoints

#### 1. Create Session
```http
POST /api/chat/sessions/create
Content-Type: application/json

{
  "config": {
    "aiProvider": "claude",
    "pageContext": {
      "url": "https://example.com",
      "title": "Example"
    }
  }
}

Response 201:
{
  "sessionId": "uuid",
  "config": {
    "botName": "AI Assistant",
    "aiProvider": "claude",
    ...
  },
  "status": "created",
  "timestamp": "2025-10-08T12:00:00Z"
}
```

#### 2. Get Session Details
```http
GET /api/chat/sessions/{session_id}
X-API-Key: cb_your_api_key (optional)

Response 200:
{
  "sessionId": "uuid",
  "config": {...},
  "messageCount": 10,
  "hasFile": false,
  "createdAt": "2025-10-08T12:00:00Z",
  "lastActivity": "2025-10-08T12:30:00Z"
}
```

#### 3. Update Session Config
```http
PUT /api/chat/sessions/{session_id}/config
Content-Type: application/json

{
  "config": {
    "aiProvider": "openai",
    "customInstructions": "Be helpful"
  }
}

Response 200:
{
  "sessionId": "uuid",
  "config": {...},
  "status": "updated"
}
```

#### 4. Get Session Stats
```http
GET /api/chat/sessions/stats/summary

Response 200:
{
  "totalSessions": 100,
  "recentlyActive": 25,
  "timestamp": "2025-10-08T12:00:00Z"
}
```

#### 5. Get Bot Configuration
```http
GET /api/chat/sessions/bot-config

Response 200:
{
  "botName": "AI Assistant",
  "poweredBy": "Claude",
  "botColor": "#667eea",
  "botIcon": "https://...",
  "botMsgBgColor": "#667eea"
}
```

---

### Message Endpoints

#### 1. Send Message
```http
POST /api/chat/messages/send
Content-Type: application/json
X-API-Key: cb_your_api_key (optional)

{
  "sessionId": "uuid",
  "message": "What is AI?",
  "config": {
    "aiProvider": "claude"
  }
}

Response 200:
{
  "response": "AI is artificial intelligence...",
  "sessionId": "uuid",
  "messageCount": 2,
  "provider": "claude",
  "model": "claude-3-5-haiku-20241022",
  "timestamp": "2025-10-08T12:00:00Z"
}
```

**Features:**
- Creates user and assistant Message objects in database
- Builds context from last 10 messages
- Includes file data if available
- Stores provider/model in message metadata
- Updates session last_activity

#### 2. Get Message History
```http
GET /api/chat/messages/history/{session_id}
X-API-Key: cb_your_api_key (optional)

Response 200:
{
  "sessionId": "uuid",
  "messages": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": 1759902466930
    },
    {
      "role": "assistant",
      "content": "Hi! How can I help?",
      "timestamp": 1759902466933,
      "provider": "claude",
      "model": "claude-3-5-haiku-20241022"
    }
  ],
  "messageCount": 2
}
```

#### 3. Clear Message History
```http
DELETE /api/chat/messages/clear/{session_id}
X-API-Key: cb_your_api_key (optional)

Response 200:
{
  "sessionId": "uuid",
  "status": "cleared",
  "messagesCleared": 10,
  "timestamp": "2025-10-08T12:00:00Z"
}
```

**Note:** Permanently deletes all Message objects for the session.

---

### File Endpoints

#### 1. Upload File
```http
POST /api/chat/files/upload
Content-Type: multipart/form-data
X-API-Key: cb_your_api_key (optional)

Form Data:
- sessionId: uuid
- file: [CSV or JSON file]

Response 200:
{
  "sessionId": "uuid",
  "file": {
    "name": "data.csv",
    "type": "csv",
    "size": 1024,
    "summary": "Customer data with 100 records",
    "rows": 100,
    "columns": ["id", "name", "email"]
  },
  "status": "uploaded"
}
```

#### 2. Get File Info
```http
GET /api/chat/files/info/{session_id}
X-API-Key: cb_your_api_key (optional)

Response 200:
{
  "hasFile": true,
  "file": {
    "name": "data.csv",
    "type": "csv",
    "size": 1024,
    "summary": "...",
    "uploadedAt": 1759902466930
  }
}
```

#### 3. Query File Data
```http
POST /api/chat/files/query/{session_id}
Content-Type: application/json

{
  "query": "customer"
}

Response 200:
{
  "results": [...],
  "count": 5
}
```

#### 4. Delete File
```http
DELETE /api/chat/files/{session_id}
X-API-Key: cb_your_api_key (optional)

Response 200:
{
  "status": "deleted",
  "sessionId": "uuid"
}
```

---

## Services

### ChatService (`chat/services/chat_service.py`)

Handles context building and token management.

**Key Methods:**

#### 1. `build_context_prompt(message, config, conversation_history, file_data)`
Builds a comprehensive context prompt for the AI provider.

```python
from chat.services import ChatService

context = ChatService.build_context_prompt(
    message="What are the top products?",
    config={
        "pageContext": {
            "url": "https://example.com/dashboard",
            "title": "Dashboard"
        },
        "customInstructions": "Be concise"
    },
    conversation_history=[
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"}
    ],
    file_data={
        "type": "csv",
        "summary": "Product data",
        "data": [...]
    }
)
```

**Context Structure:**
1. Page context (URL, title, content)
2. Custom instructions
3. JSON/CSV data with summary
4. Conversation history (last 10 messages)
5. Current user message

**Token Management:**
- `MAX_TOTAL_TOKENS = 6000` (leaves ~2k for response)
- `MAX_USER_MESSAGE_TOKENS = 3000`
- `MAX_JSON_DATA_TOKENS = 2000`
- `MAX_HISTORY_TOKENS = 1500`

#### 2. `estimate_token_count(text)`
Estimates token count for text (rough approximation).

```python
token_count = ChatService.estimate_token_count("Hello, world!")
# Returns: 3
```

#### 3. `process_json_data_to_csv(data)`
Converts large JSON arrays to CSV format for token efficiency.

```python
csv_sections = ChatService.process_json_data_to_csv({
    "campaigns": [
        {"id": 1, "name": "Campaign A"},
        {"id": 2, "name": "Campaign B"}
    ]
})
# Returns: ["campaigns:\nid,name\n1,Campaign A\n2,Campaign B"]
```

---

### FileProcessor (`chat/services/file_processor.py`)

Handles file parsing and analysis.

**Key Methods:**

#### 1. `process_file(file, file_type)`
Processes uploaded file and returns structured data.

```python
from chat.services import FileProcessor

result = FileProcessor.process_file(file, "csv")
# Returns: {
#     "type": "csv",
#     "name": "data.csv",
#     "size": 1024,
#     "data": [...],
#     "summary": "CSV file with 100 rows",
#     "columns": ["id", "name"],
#     "rows": 100
# }
```

#### 2. `parse_csv(file_content)`
Parses CSV file content.

#### 3. `parse_json(file_content)`
Parses JSON file content.

#### 4. `analyze_data_types(data)`
Analyzes data types in structured data.

#### 5. `generate_summary(data, file_type)`
Generates AI-powered summary of file contents.

---

## Configuration

### Settings (`config/settings/base.py`)

```python
# Session timeout (30 minutes)
CHAT_SESSION_TIMEOUT = 30 * 60

# File upload max size (10MB)
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# AI Provider settings
AI_PROVIDER = env("AI_PROVIDER", default="claude")
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default=None)
OPENAI_API_KEY = env("OPENAI_API_KEY", default=None)
ENABLE_DUMMY_PROVIDER = env("ENABLE_DUMMY_PROVIDER", default=False)

# Model configuration
CLAUDE_MODEL = env("CLAUDE_MODEL", default="claude-3-5-haiku-20241022")
OPENAI_MODEL = env("OPENAI_MODEL", default="gpt-4o")
DUMMY_MODEL = env("DUMMY_MODEL", default="dummy-1.0")

# Bot configuration
BOT_NAME = env("BOT_NAME", default="Claude Assistant")
BOT_POWERED_BY = env("BOT_POWERED_BY", default="Claude")
BOT_COLOR = env("BOT_COLOR", default="#667eea")
BOT_MSG_BG_COLOR = env("BOT_MSG_BG_COLOR", default="#667eea")
BOT_ICON = env("BOT_ICON", default=None)
```

### URL Configuration (`chat/urls.py`)

```python
from django.urls import path
from chat import views

urlpatterns = [
    # Sessions
    path("sessions/create", views.SessionCreateView.as_view(), name="session-create"),
    path("sessions/<uuid:session_id>", views.SessionDetailView.as_view(), name="session-detail"),
    path("sessions/<uuid:session_id>/config", views.SessionConfigUpdateView.as_view(), name="session-config-update"),
    path("sessions/stats/summary", views.SessionStatsView.as_view(), name="session-stats"),
    path("sessions/bot-config", views.BotConfigView.as_view(), name="bot-config"),

    # Messages
    path("messages/send", views.ChatMessageView.as_view(), name="chat-message"),
    path("messages/history/<uuid:session_id>", views.ChatHistoryView.as_view(), name="chat-history"),
    path("messages/clear/<uuid:session_id>", views.ClearHistoryView.as_view(), name="chat-clear-history"),

    # Files
    path("files/upload", views.FileUploadView.as_view(), name="file-upload"),
    path("files/info/<uuid:session_id>", views.FileInfoView.as_view(), name="file-info"),
    path("files/query/<uuid:session_id>", views.FileQueryView.as_view(), name="file-query"),
    path("files/<uuid:session_id>", views.FileDeleteView.as_view(), name="file-delete"),
]
```

---

## Usage Examples

### 1. Basic Chat Flow

```python
import requests

BASE_URL = "http://localhost:8000/api/chat"

# 1. Create session
response = requests.post(f"{BASE_URL}/sessions/create", json={
    "config": {"aiProvider": "claude"}
})
session_id = response.json()["sessionId"]

# 2. Send message
response = requests.post(f"{BASE_URL}/messages/send", json={
    "sessionId": session_id,
    "message": "What is Python?"
})
print(response.json()["response"])

# 3. Get history
response = requests.get(f"{BASE_URL}/messages/history/{session_id}")
messages = response.json()["messages"]

# 4. Clear history
requests.delete(f"{BASE_URL}/messages/clear/{session_id}")
```

### 2. File Upload & Analysis

```python
# 1. Upload CSV file
files = {"file": open("data.csv", "rb")}
data = {"sessionId": session_id}
response = requests.post(
    f"{BASE_URL}/files/upload",
    files=files,
    data=data
)

# 2. Ask questions about the file
response = requests.post(f"{BASE_URL}/messages/send", json={
    "sessionId": session_id,
    "message": "What are the top 5 products by revenue?"
})
print(response.json()["response"])

# 3. Query file data
response = requests.post(f"{BASE_URL}/files/query/{session_id}", json={
    "query": "revenue"
})
print(response.json()["results"])
```

### 3. Multi-Tenant with API Key

```python
API_KEY = "cb_your_api_key_here"
headers = {"X-API-Key": API_KEY}

# Create session for specific client
response = requests.post(
    f"{BASE_URL}/sessions/create",
    headers=headers,
    json={"config": {"aiProvider": "claude"}}
)

# Send message (ownership automatically verified)
response = requests.post(
    f"{BASE_URL}/messages/send",
    headers=headers,
    json={
        "sessionId": session_id,
        "message": "Hello!"
    }
)
```

---

## Database Queries

### Common Queries

```python
from chat.models import Session, Message, FileUpload
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

# Get active sessions (not expired)
thirty_min_ago = timezone.now() - timedelta(minutes=30)
active_sessions = Session.objects.filter(
    last_activity__gte=thirty_min_ago
)

# Get sessions with messages
sessions_with_messages = Session.objects.annotate(
    msg_count=Count('conversation_messages')
).filter(msg_count__gt=0)

# Get recent messages
recent_messages = Message.objects.filter(
    timestamp__gte=timezone.now() - timedelta(hours=24)
).order_by('-timestamp')

# Get user vs assistant message counts
message_stats = Message.objects.values('role').annotate(
    count=Count('id')
)

# Get sessions with files
sessions_with_files = Session.objects.filter(
    uploaded_files__is_active=True
).distinct()

# Get messages by provider
claude_messages = Message.objects.filter(
    metadata__provider='claude'
)

# Full-text search in messages
search_messages = Message.objects.filter(
    content__icontains='python'
)

# Get conversation thread
conversation = Message.objects.filter(
    session_id=session_id
).order_by('timestamp')
```

### Analytics Queries

```python
from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncDate

# Messages per day
messages_per_day = Message.objects.annotate(
    date=TruncDate('timestamp')
).values('date').annotate(
    count=Count('id')
).order_by('-date')

# Average messages per session
avg_messages = Session.objects.annotate(
    msg_count=Count('conversation_messages')
).aggregate(
    average=Avg('msg_count')
)

# Most active sessions
active_sessions = Session.objects.annotate(
    msg_count=Count('conversation_messages')
).order_by('-msg_count')[:10]

# Client statistics (if multi-tenant)
from clients.models import Client
client_stats = Client.objects.annotate(
    session_count=Count('sessions'),
    message_count=Count('sessions__conversation_messages')
)
```

---

## Testing

### Unit Tests

```python
from django.test import TestCase
from chat.models import Session, Message

class MessageModelTest(TestCase):
    def setUp(self):
        self.session = Session.objects.create(
            config={"aiProvider": "dummy"}
        )

    def test_create_message(self):
        msg = Message.objects.create(
            session=self.session,
            role="user",
            content="Test message"
        )
        self.assertEqual(msg.role, "user")
        self.assertEqual(msg.content, "Test message")

    def test_message_to_dict(self):
        msg = Message.objects.create(
            session=self.session,
            role="assistant",
            content="Response",
            metadata={"provider": "claude"}
        )
        data = msg.to_dict()
        self.assertIn("provider", data)
        self.assertEqual(data["provider"], "claude")
```

### API Tests

```python
from django.test import TestCase
from rest_framework.test import APIClient

class ChatAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_session(self):
        response = self.client.post('/api/chat/sessions/create', {
            "config": {"aiProvider": "dummy"}
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIn("sessionId", response.json())

    def test_send_message(self):
        # Create session
        session_response = self.client.post(
            '/api/chat/sessions/create',
            {"config": {"aiProvider": "dummy"}},
            format='json'
        )
        session_id = session_response.json()["sessionId"]

        # Send message
        response = self.client.post('/api/chat/messages/send', {
            "sessionId": session_id,
            "message": "Test",
            "config": {"aiProvider": "dummy"}
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertIn("response", response.json())
        self.assertEqual(response.json()["messageCount"], 2)
```

### Manual Testing

```bash
# 1. Create session
curl -X POST http://localhost:8000/api/chat/sessions/create \
  -H "Content-Type: application/json" \
  -d '{"config":{"aiProvider":"dummy"}}'

# 2. Send message
curl -X POST http://localhost:8000/api/chat/messages/send \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId":"uuid-here",
    "message":"Hello!",
    "config":{"aiProvider":"dummy"}
  }'

# 3. Get history
curl http://localhost:8000/api/chat/messages/history/uuid-here

# 4. Clear history
curl -X DELETE http://localhost:8000/api/chat/messages/clear/uuid-here
```

---

## Performance Optimization

### Database Indexes

All critical queries are optimized with indexes:

```sql
-- Session queries
CREATE INDEX chatbot_ses_last_ac_51af55_idx
ON chatbot_sessions_session(last_activity DESC);

-- Message queries
CREATE INDEX conversatio_session_c9e0af_idx
ON conversation_messages(session_id, timestamp);

CREATE INDEX conversatio_session_a27a84_idx
ON conversation_messages(session_id, timestamp DESC);

-- File queries
CREATE INDEX file_upload_session_83fd7f_idx
ON file_uploads(session_id, uploaded_at DESC);

CREATE INDEX file_upload_session_3753b7_idx
ON file_uploads(session_id, is_active);
```

### Query Optimization Tips

```python
# Use select_related for foreign keys
session = Session.objects.select_related('client').get(id=session_id)

# Use prefetch_related for reverse relations
session = Session.objects.prefetch_related('conversation_messages').get(id=session_id)

# Limit message queries
recent_messages = session.conversation_messages.order_by('-timestamp')[:10]

# Use only() to select specific fields
messages = Message.objects.only('role', 'content', 'timestamp')

# Use values() for data extraction
message_data = Message.objects.filter(session=session).values('role', 'content')

# Bulk create for multiple messages
Message.objects.bulk_create([
    Message(session=session, role='user', content='Hello'),
    Message(session=session, role='assistant', content='Hi')
])
```

### Caching Strategy

```python
from django.core.cache import cache

# Cache session config
def get_session_config(session_id):
    cache_key = f"session_config_{session_id}"
    config = cache.get(cache_key)

    if config is None:
        session = Session.objects.get(id=session_id)
        config = session.config
        cache.set(cache_key, config, timeout=300)  # 5 minutes

    return config

# Cache message count
def get_message_count(session_id):
    cache_key = f"message_count_{session_id}"
    count = cache.get(cache_key)

    if count is None:
        count = Message.objects.filter(session_id=session_id).count()
        cache.set(cache_key, count, timeout=60)  # 1 minute

    return count
```

---

## Troubleshooting

### Common Issues

#### 1. Session Not Found
```
Error: Session not found
```

**Causes:**
- Session ID is incorrect
- Session belongs to different client (multi-tenant)
- Session was deleted

**Solution:**
```python
# Verify session exists
from chat.models import Session
try:
    session = Session.objects.get(id=session_id)
    print(f"Session found: {session.id}")
except Session.DoesNotExist:
    print("Session does not exist")

# Check client ownership
if session.client:
    print(f"Session belongs to: {session.client.email}")
```

#### 2. No Messages Returned
```
Response: {"messages": [], "messageCount": 0}
```

**Causes:**
- Messages not created in database
- Wrong session ID
- Messages deleted

**Solution:**
```python
# Check message count in database
from chat.models import Message
count = Message.objects.filter(session_id=session_id).count()
print(f"Messages in DB: {count}")

# Check recent messages
messages = Message.objects.filter(session_id=session_id).order_by('-timestamp')
for msg in messages:
    print(f"{msg.role}: {msg.content[:50]}")
```

#### 3. AI Provider Errors
```
Error: Failed to process message
```

**Causes:**
- Invalid API key
- Provider not available
- Rate limiting

**Solution:**
```python
# Check available providers
from ai_providers import ai_provider
print(f"Available providers: {ai_provider.get_available_providers()}")

# Test provider
try:
    import asyncio
    response = asyncio.run(ai_provider.generate_response(
        "dummy",
        [{"role": "user", "content": "test"}],
        {}
    ))
    print(f"Provider works: {response}")
except Exception as e:
    print(f"Provider error: {e}")
```

#### 4. File Upload Issues
```
Error: File upload failed
```

**Causes:**
- File too large
- Unsupported file type
- Invalid file format

**Solution:**
```python
# Check file size limit
from django.conf import settings
max_size = settings.FILE_UPLOAD_MAX_MEMORY_SIZE
print(f"Max file size: {max_size / (1024*1024)}MB")

# Verify file type
allowed_types = ['json', 'csv']
print(f"Allowed types: {allowed_types}")
```

---

## Migration Guide

### From Legacy JSONField to Message Model

If you have existing sessions with messages in the legacy `session.messages` JSONField:

```python
from chat.models import Session, Message

def migrate_legacy_messages():
    """Migrate messages from JSONField to Message model"""
    sessions = Session.objects.exclude(messages=[])

    for session in sessions:
        if session.messages:
            # Create Message objects from JSON
            for msg_data in session.messages:
                Message.objects.create(
                    session=session,
                    role=msg_data.get('role', 'user'),
                    content=msg_data['content'],
                    metadata={
                        k: v for k, v in msg_data.items()
                        if k not in ['role', 'content', 'timestamp']
                    }
                )

            print(f"Migrated {len(session.messages)} messages for session {session.id}")

    print("Migration complete!")

# Run migration
migrate_legacy_messages()
```

---

## Best Practices

### 1. Session Management
- Create one session per conversation
- Update session config when AI provider changes
- Clean up expired sessions periodically
- Use session.update_activity() to prevent expiration

### 2. Message Storage
- Always create Message objects (don't use legacy JSONField)
- Include metadata for assistant messages (provider, model)
- Use pagination for large conversation histories
- Delete messages when clearing history

### 3. Context Building
- Keep messages under token limits
- Include only relevant context
- Convert large JSON to CSV format
- Limit conversation history to last 10 messages

### 4. File Handling
- Validate file type and size before upload
- Generate AI summaries for better context
- Store files in secure location
- Clean up old files periodically

### 5. Error Handling
- Always catch Session.DoesNotExist
- Verify client ownership in multi-tenant setup
- Log errors with context
- Return appropriate HTTP status codes

---

## Security Considerations

### 1. API Key Authentication
```python
# All sensitive endpoints require authentication
@method_decorator(ensure_csrf_cookie, name='dispatch')
class ChatMessageView(APIView):
    def post(self, request):
        client = request.auth  # Authenticated client or None
        # Verify ownership before proceeding
```

### 2. Input Validation
```python
# Validate session ID format
import uuid
try:
    uuid.UUID(session_id)
except ValueError:
    return Response({"error": "Invalid session ID"}, status=400)

# Validate message length
if len(message) > 10000:
    return Response({"error": "Message too long"}, status=400)
```

### 3. Rate Limiting
```python
# Implement rate limiting per client
from django_ratelimit.decorators import ratelimit

@ratelimit(key='header:X-API-Key', rate='100/h')
def send_message(request):
    # Process message
    pass
```

### 4. Data Sanitization
```python
# Sanitize file uploads
import magic
file_type = magic.from_buffer(file.read(1024), mime=True)
if file_type not in ['text/csv', 'application/json']:
    raise ValueError("Unsupported file type")
```

---

## Changelog

### Version 2.0 (October 8, 2025)
- ✅ Migrated to normalized Message model
- ✅ Consolidated into single chat/ app
- ✅ Added database indexes for performance
- ✅ Unified URL structure under /api/chat/
- ✅ Added message metadata support
- ✅ Improved token management

### Version 1.0 (October 6, 2025)
- Initial implementation with JSONField storage
- Multi-tenant support
- File upload functionality
- AI provider integration

---

## Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **DRF Documentation**: https://www.django-rest-framework.org/
- **Claude API**: https://docs.anthropic.com/
- **OpenAI API**: https://platform.openai.com/docs/

---

**Documentation Last Updated**: October 8, 2025
**Maintained By**: Development Team
**Questions?** Check `/Documentation/multi_tenant_implementation.md` for multi-tenant setup.
