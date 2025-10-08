# Chat App - Complete Documentation

**Version**: 2.1
**Date**: October 9, 2025
**Status**: Production Ready

---

## Overview

The `chat/` app is a unified Django application that handles all chat-related functionality including sessions, messages, and file uploads. It provides a complete conversational AI interface with normalized database storage, multi-provider support, and file analysis capabilities.

### Key Features

- **Session Management**: Create and manage chat sessions with custom configurations
- **User Tracking**: Track individual users with `user_identifier` field for analytics
- **Message Storage**: Normalized database storage for all conversation messages
- **AI Provider Integration**: Support for Claude, OpenAI, and custom providers
- **File Upload & Analysis**: JSON/CSV file upload with AI-powered analysis
- **Multi-Tenant Support**: Client isolation with mandatory API key authentication
- **Secure API Access**: All endpoints require X-API-Key header (returns 401 without valid key)
- **Context Building**: Smart context management with token limits
- **Message History**: Full conversation history with chronological ordering
- **Analytics**: User engagement metrics and session statistics by user

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
- `user_identifier` (CharField): Identifies the end-user within a client (e.g., email, UUID)
- `config` (JSONField): Session configuration (AI provider, page context, etc.)
- `messages` (JSONField): Legacy field, no longer used
- `file_data` (JSONField): Legacy field for file data
- `created_at` (DateTime): Auto-set on creation
- `last_activity` (DateTime): Auto-updated on save

**Database Table**: `chatbot_sessions_session`

**Indexes:**
- `chatbot_ses_last_ac_51af55_idx` on `-last_activity`
- `chatbot_ses_user_id_78bc44_idx` on `user_identifier` for analytics queries

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

### Authentication

**IMPORTANT**: All chat API endpoints require authentication via `X-API-Key` header. Requests without a valid API key will be rejected with a 401 Unauthorized error.

```http
X-API-Key: cb_your_api_key_here
```

**Error Response (Missing/Invalid API Key):**
```json
HTTP 401 Unauthorized
{
  "error": "Authentication required",
  "detail": "Valid API key must be provided in X-API-Key header"
}
```

### Session Endpoints

#### 1. Create Session
```http
POST /api/chat/sessions/create
Content-Type: application/json
X-API-Key: cb_your_api_key_here

{
  "config": {
    "aiProvider": "claude",
    "pageContext": {
      "url": "https://example.com",
      "title": "Example"
    }
  },
  "user_identifier": "user@example.com"  // Optional: track end-user
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

**Parameters:**
- `config` (required): Session configuration object
- `user_identifier` (optional): Unique identifier for the end-user (email, UUID, etc.)

#### 2. Get Session Details
```http
GET /api/chat/sessions/{session_id}
X-API-Key: cb_your_api_key_here

Response 200:
{
  "sessionId": "uuid",
  "config": {...},
  "messageCount": 10,
  "hasFile": false,
  "createdAt": "2025-10-08T12:00:00Z",
  "lastActivity": "2025-10-08T12:30:00Z"
}`
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

#### 4. Get Session Stats Summary
```http
GET /api/chat/sessions/stats/summary

Response 200:
{
  "totalSessions": 100,
  "recentlyActive": 25,
  "timestamp": "2025-10-08T12:00:00Z"
}
```

#### 5. Get Session Stats by User
```http
GET /api/chat/sessions/stats/by-user
X-API-Key: cb_your_api_key_here

Response 200:
{
  "userStats": {
    "user1@example.com": 5,
    "user2@example.com": 3,
    "anonymous-uuid-123": 2
  },
  "summary": {
    "totalSessions": 34,
    "sessionsWithUser": 10,
    "sessionsWithoutUser": 24,
    "uniqueUsers": 3
  }
}
```

**Description:** Returns session counts grouped by `user_identifier` for analytics and user tracking.

#### 6. Get Bot Configuration
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
X-API-Key: cb_your_api_key_here

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
X-API-Key: cb_your_api_key_here

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
X-API-Key: cb_your_api_key_here

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
X-API-Key: cb_your_api_key_here

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
X-API-Key: cb_your_api_key_here

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
X-API-Key: cb_your_api_key_here

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
    path("sessions/stats/by-user", views.SessionUserStatsView.as_view(), name="session-user-stats"),
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
API_KEY = "cb_your_api_key_here"
headers = {"X-API-Key": API_KEY}

# 1. Create session with user tracking
response = requests.post(
    f"{BASE_URL}/sessions/create",
    headers=headers,
    json={
        "config": {"aiProvider": "claude"},
        "user_identifier": "user123@example.com"  # Track this specific user
    }
)
session_id = response.json()["sessionId"]

# 2. Send message
response = requests.post(
    f"{BASE_URL}/messages/send",
    headers=headers,
    json={
        "sessionId": session_id,
        "message": "What is Python?"
    }
)
print(response.json()["response"])

# 3. Get history
response = requests.get(
    f"{BASE_URL}/messages/history/{session_id}",
    headers=headers
)
messages = response.json()["messages"]

# 4. Clear history
requests.delete(
    f"{BASE_URL}/messages/clear/{session_id}",
    headers=headers
)
```

### 2. File Upload & Analysis

```python
API_KEY = "cb_your_api_key_here"
headers = {"X-API-Key": API_KEY}

# 1. Upload CSV file
files = {"file": open("data.csv", "rb")}
data = {"sessionId": session_id}
response = requests.post(
    f"{BASE_URL}/files/upload",
    headers=headers,
    files=files,
    data=data
)

# 2. Ask questions about the file
response = requests.post(
    f"{BASE_URL}/messages/send",
    headers=headers,
    json={
        "sessionId": session_id,
        "message": "What are the top 5 products by revenue?"
    }
)
print(response.json()["response"])

# 3. Query file data
response = requests.post(
    f"{BASE_URL}/files/query/{session_id}",
    headers=headers,
    json={"query": "revenue"}
)
print(response.json()["results"])
```

### 3. User Tracking & Analytics

```python
API_KEY = "cb_your_api_key_here"
headers = {"X-API-Key": API_KEY}

# Get user statistics
response = requests.get(
    f"{BASE_URL}/sessions/stats/by-user",
    headers=headers
)
stats = response.json()

print(f"Total sessions: {stats['summary']['totalSessions']}")
print(f"Unique users: {stats['summary']['uniqueUsers']}")

# Print sessions per user
for user, count in stats['userStats'].items():
    print(f"{user}: {count} sessions")

# Query sessions for specific user (Django shell)
from chat.models import Session
user_sessions = Session.objects.filter(user_identifier='user123@example.com')
print(f"Sessions for user123: {user_sessions.count()}")
```

### 4. Multi-Tenant with API Key

```python
API_KEY = "cb_your_api_key_here"
headers = {"X-API-Key": API_KEY}

# Create session for specific client with user tracking
response = requests.post(
    f"{BASE_URL}/sessions/create",
    headers=headers,
    json={
        "config": {"aiProvider": "claude"},
        "user_identifier": "customer@clientdomain.com"
    }
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

# Get user stats for this client
response = requests.get(
    f"{BASE_URL}/sessions/stats/by-user",
    headers=headers
)
print(response.json())
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

# Get sessions by user identifier
user_sessions = Session.objects.filter(
    user_identifier='user@example.com'
).order_by('-created_at')

# Count sessions per user
from django.db.models import Count
user_session_counts = Session.objects.values('user_identifier').annotate(
    session_count=Count('id')
).order_by('-session_count')

# Get sessions without user tracking
anonymous_sessions = Session.objects.filter(
    user_identifier__isnull=True
) | Session.objects.filter(user_identifier='')

# Get unique users
unique_users = Session.objects.exclude(
    user_identifier__isnull=True
).exclude(
    user_identifier=''
).values_list('user_identifier', flat=True).distinct()
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

# User engagement metrics
user_engagement = Session.objects.values('user_identifier').annotate(
    total_sessions=Count('id'),
    total_messages=Count('conversation_messages'),
    first_session=Min('created_at'),
    last_session=Max('last_activity')
).order_by('-total_sessions')

# Active users in last 24 hours
from django.utils import timezone
from datetime import timedelta
active_users = Session.objects.filter(
    last_activity__gte=timezone.now() - timedelta(hours=24)
).values('user_identifier').distinct().count()

# Sessions per user over time
from django.db.models.functions import TruncDate
sessions_per_user_per_day = Session.objects.annotate(
    date=TruncDate('created_at')
).values('date', 'user_identifier').annotate(
    count=Count('id')
).order_by('-date')
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
from clients.models import Client

class ChatAPITest(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(
            name="Test Client",
            email="test@example.com"
        )
        self.api_client = APIClient()
        # Set API key in header
        self.api_client.credentials(HTTP_X_API_KEY=self.client_obj.api_key)

    def test_create_session_with_auth(self):
        """Test session creation with valid API key"""
        response = self.api_client.post('/api/chat/sessions/create', {
            "config": {"aiProvider": "dummy"},
            "user_identifier": "test_user@example.com"
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIn("sessionId", response.json())

    def test_create_session_without_auth(self):
        """Test session creation without API key fails"""
        # Clear credentials
        client_no_auth = APIClient()
        response = client_no_auth.post('/api/chat/sessions/create', {
            "config": {"aiProvider": "dummy"}
        }, format='json')
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json())

    def test_send_message(self):
        """Test sending message with authentication"""
        # Create session
        session_response = self.api_client.post(
            '/api/chat/sessions/create',
            {"config": {"aiProvider": "dummy"}},
            format='json'
        )
        session_id = session_response.json()["sessionId"]

        # Send message
        response = self.api_client.post('/api/chat/messages/send', {
            "sessionId": session_id,
            "message": "Test",
            "config": {"aiProvider": "dummy"}
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertIn("response", response.json())
        self.assertEqual(response.json()["messageCount"], 2)

    def test_get_user_stats(self):
        """Test getting user statistics"""
        response = self.api_client.get('/api/chat/sessions/stats/by-user')
        self.assertEqual(response.status_code, 200)
        self.assertIn("userStats", response.json())
        self.assertIn("summary", response.json())
```

### Manual Testing

```bash
# Set your API key
API_KEY="cb_your_api_key_here"

# 1. Create session
curl -X POST http://localhost:8000/api/chat/sessions/create \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"config":{"aiProvider":"claude"},"user_identifier":"test@example.com"}'

# 2. Send message
curl -X POST http://localhost:8000/api/chat/messages/send \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "sessionId":"uuid-here",
    "message":"Hello!",
    "config":{"aiProvider":"claude"}
  }'

# 3. Get history
curl http://localhost:8000/api/chat/messages/history/uuid-here \
  -H "X-API-Key: $API_KEY"

# 4. Clear history
curl -X DELETE http://localhost:8000/api/chat/messages/clear/uuid-here \
  -H "X-API-Key: $API_KEY"

# 5. Get user statistics
curl http://localhost:8000/api/chat/sessions/stats/by-user \
  -H "X-API-Key: $API_KEY"

# Error: Missing API key
curl -X POST http://localhost:8000/api/chat/sessions/create \
  -H "Content-Type: application/json" \
  -d '{"config":{"aiProvider":"claude"}}'
# Response: 401 Unauthorized - Authentication required
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

## Widget Integration & User Tracking

### Overview

The chatbot widget provides embedded chat functionality with automatic user tracking. Widget files are served from `static/widget/` and `templates/widget/` directories.

### User Identification

The widget supports three modes of user identification:

1. **Explicit User Identifier** - Specify via URL parameter
2. **Auto-Generated UUID** - Automatically created and stored in localStorage
3. **No Tracking** - Sessions created without user_identifier

### Widget Embedding

#### Option 1: With Specific User (Recommended for authenticated users)

```html
<script src="https://your-domain.com/widget/chatbot.js?apiKey=cb_xxx&userIdentifier=user@example.com"></script>
```

#### Option 2: Auto-Generate UUID (For anonymous tracking)

```html
<script src="https://your-domain.com/widget/chatbot.js?apiKey=cb_xxx"></script>
```

The widget will:
- Generate a unique UUID on first visit
- Store it in localStorage as `chatbot_user_id`
- Use it for all subsequent sessions
- Persist across browser sessions

#### Option 3: No User Tracking

```html
<script src="https://your-domain.com/widget/chatbot.js?apiKey=cb_xxx&noTracking=true"></script>
```

### User Tracking Flow

```
User visits page
    ↓
Widget loads → Check localStorage for chatbot_user_id
    ↓
If exists → Use stored UUID
    ↓
If not → Generate new UUID → Store in localStorage
    ↓
Create session with user_identifier
    ↓
All messages linked to this user
```

### PostMessage API

The widget communicates with the parent page via PostMessage API:

```javascript
// Listen for widget events
window.addEventListener('message', (event) => {
    if (event.data.type === 'widget_ready') {
        console.log('Widget loaded');
    }

    if (event.data.type === 'session_created') {
        console.log('Session ID:', event.data.sessionId);
        console.log('User ID:', event.data.userId);
    }

    if (event.data.type === 'message_received') {
        console.log('Message:', event.data.message);
    }

    if (event.data.type === 'widget_minimized') {
        console.log('Widget minimized');
    }
});
```

### Analytics Integration

Track user behavior with the widget:

```javascript
// Custom analytics tracking
window.addEventListener('message', (event) => {
    if (event.data.type === 'session_created') {
        // Track session creation
        analytics.track('Chat Session Created', {
            userId: event.data.userId,
            sessionId: event.data.sessionId
        });
    }

    if (event.data.type === 'message_received') {
        // Track bot responses
        analytics.track('Bot Message Received', {
            userId: event.data.userId,
            messageLength: event.data.message.length
        });
    }
});
```

### User Statistics API

Query user activity via the API:

```python
import requests

# Get all user statistics
response = requests.get('http://localhost:8000/api/chat/sessions/stats/by-user')
stats = response.json()

# Process user data
for user_id, session_count in stats['userStats'].items():
    if user_id.startswith('user@'):
        print(f"Authenticated user {user_id}: {session_count} sessions")
    elif len(user_id) == 36:  # UUID format
        print(f"Anonymous user {user_id}: {session_count} sessions")
```

### Django Admin Integration

View user statistics in Django Admin:

```python
# chat/admin.py
from django.contrib import admin
from django.db.models import Count
from chat.models import Session

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_identifier', 'client', 'created_at', 'message_count']
    list_filter = ['client', 'created_at']
    search_fields = ['id', 'user_identifier', 'client__email']

    def message_count(self, obj):
        return obj.conversation_messages.count()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(msg_count=Count('conversation_messages'))
```

### Privacy Considerations

- **UUID Storage**: UUIDs stored in localStorage are client-side only
- **No PII**: Auto-generated UUIDs contain no personally identifiable information
- **User Control**: Users can clear localStorage to reset tracking
- **GDPR Compliance**: Allow users to request data deletion via API

### Advanced: Custom User Identification

Integrate with your authentication system:

```javascript
// Get current user from your app
const currentUser = getCurrentUser();  // Your auth function

// Pass to widget
const widgetScript = document.createElement('script');
widgetScript.src = `https://your-domain.com/widget/chatbot.js?apiKey=cb_xxx&userIdentifier=${currentUser.email}`;
document.body.appendChild(widgetScript);
```

---

## Best Practices

### 0. Authentication (CRITICAL)
- **ALWAYS** include `X-API-Key` header in all API requests
- Never hardcode API keys in client-side JavaScript
- Store API keys in environment variables or secure key management systems
- Use HTTPS in production to protect API keys in transit
- Rotate API keys periodically for security
- Monitor API usage for unauthorized access attempts

### 1. Session Management
- Create one session per conversation
- Always include `user_identifier` when creating sessions for analytics
- Update session config when AI provider changes
- Clean up expired sessions periodically
- Use session.update_activity() to prevent expiration
- Filter sessions by client in multi-tenant setups

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

### 6. User Tracking
- Use meaningful user identifiers (email, username, etc.) for authenticated users
- Let widget auto-generate UUIDs for anonymous users
- Index `user_identifier` field for better query performance
- Track user engagement with `/api/chat/sessions/stats/by-user` endpoint
- Regularly analyze user statistics for insights
- Respect user privacy - don't store PII unnecessarily
- Implement data retention policies for GDPR compliance

---

## Security Considerations

### 1. API Key Authentication (REQUIRED)

**CRITICAL**: All chat API endpoints require a valid API key in the `X-API-Key` header. Requests without authentication will be rejected with HTTP 401 Unauthorized.

```python
# All chat endpoints require authentication
from rest_framework.permissions import IsAuthenticated
from core.authentication import APIKeyAuthentication

class ChatMessageView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        client = request.auth  # Authenticated client object
        # Client ownership automatically verified
        # Proceed with request
```

**Error Handling:**
```python
# Missing API key
HTTP 401 Unauthorized
{
    "error": "Authentication required",
    "detail": "Valid API key must be provided in X-API-Key header"
}

# Invalid API key
HTTP 401 Unauthorized
{
    "error": "Invalid API key"
}
```

**Best Practices:**
- Never expose API keys in client-side code
- Rotate API keys periodically
- Use environment variables to store keys
- Monitor API key usage for suspicious activity
- Implement rate limiting per API key (see section 3)

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

### Version 2.1 (October 9, 2025)
- ✅ **SECURITY**: All chat API endpoints now require X-API-Key authentication
- ✅ Added user tracking with `user_identifier` field
- ✅ New endpoint: `/api/chat/sessions/stats/by-user` for user analytics
- ✅ Widget auto-generates and persists UUID in localStorage
- ✅ User identification via URL parameter support
- ✅ Enhanced Django Admin with user filtering
- ✅ Added database index on `user_identifier` for performance
- ✅ Privacy controls and GDPR compliance considerations
- ✅ Updated all examples and tests to include required authentication

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

**Documentation Last Updated**: October 9, 2025
**Maintained By**: Development Team
**Questions?** Check `/Documentation/multi_tenant_implementation.md` for multi-tenant setup.

---

## Summary of API Changes in Version 2.1

### BREAKING CHANGES - Authentication Required

**⚠️ CRITICAL**: All chat API endpoints now require authentication via `X-API-Key` header. Requests without a valid API key will be rejected with HTTP 401 Unauthorized.

**Affected Endpoints:**
- All `/api/chat/sessions/*` endpoints
- All `/api/chat/messages/*` endpoints
- All `/api/chat/files/*` endpoints

**Migration Required:**
All API clients must include the `X-API-Key` header in every request:
```http
X-API-Key: cb_your_api_key_here
```

### New Features
1. **User Tracking**: Sessions now support `user_identifier` field for tracking individual users
2. **User Stats Endpoint**: New `/api/chat/sessions/stats/by-user` endpoint for user analytics
3. **Widget User Identification**: Automatic UUID generation and localStorage persistence
4. **Enhanced Queries**: New database queries for user engagement metrics

### Updated Endpoints
- **ALL ENDPOINTS**: Now require `X-API-Key` header (BREAKING CHANGE)
- `POST /api/chat/sessions/create` - Now accepts optional `user_identifier` parameter
- `GET /api/chat/sessions/stats/by-user` - NEW: Returns session counts grouped by user

### Database Changes
- Added `user_identifier` field to Session model
- Added index on `user_identifier` for performance
- Support for tracking both authenticated users (email) and anonymous users (UUID)

### Widget Enhancements
- Auto-generates UUID for anonymous users
- Stores user ID in localStorage (`chatbot_user_id`)
- Supports explicit user identification via URL parameter
- PostMessage API includes user information in events

### Security Improvements
- Mandatory API key authentication for all chat endpoints
- Client ownership verification on all requests
- Rate limiting support per API key
- Enhanced error messages for authentication failures
