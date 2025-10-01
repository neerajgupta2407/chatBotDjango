# Django Chatbot Widget Backend

Django REST API backend for the embeddable chatbot widget, supporting Claude and OpenAI AI providers.

## Project Structure

```
backend_django/
├── config/                      # Django project configuration
│   ├── settings/
│   │   ├── base.py             # Base settings
│   │   ├── development.py      # Dev settings
│   │   ├── production.py       # Prod settings
│   │   └── testing.py          # Test settings
│   ├── urls.py                 # URL routing
│   └── wsgi.py
├── chat_sessions/              # Session management app
│   ├── models.py               # Session model
│   ├── views.py                # Session API views
│   └── urls.py
├── chat/                        # Chat messaging app
│   ├── views.py                # Chat API views
│   ├── services.py             # Context building logic
│   └── urls.py
├── files/                       # File upload app
│   ├── views.py                # File API views
│   └── urls.py
├── core/                        # Core utilities
│   ├── ai_providers.py         # AI provider factory
│   └── file_processor.py       # File processing utilities
├── static/widget/               # Frontend files
├── media/uploads/               # Uploaded files
├── manage.py
├── requirements.txt
└── .env
```

## Quick Start

### 1. Setup Virtual Environment

```bash
cd backend_django
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
```

### 4. Run Migrations

```bash
export DJANGO_SETTINGS_MODULE=config.settings.development
python manage.py migrate
```

### 5. Start Development Server

```bash
python manage.py runserver
```

The server will start on `http://localhost:8000`

## API Endpoints

### Health Check
- `GET /health` - Health check endpoint

### Sessions
- `POST /api/sessions/create` - Create new session
- `GET /api/sessions/<session_id>` - Get session details
- `PUT /api/sessions/<session_id>/config` - Update session config
- `GET /api/sessions/stats/summary` - Get session statistics
- `GET /api/sessions/bot-config` - Get bot configuration

### Chat
- `POST /api/chat/message` - Send message to AI
- `GET /api/chat/history/<session_id>` - Get conversation history
- `DELETE /api/chat/history/<session_id>` - Clear conversation history

### Files
- `POST /api/files/upload` - Upload CSV/JSON file
- `GET /api/files/info/<session_id>` - Get file information
- `POST /api/files/query/<session_id>` - Query file data
- `DELETE /api/files/<session_id>` - Delete file data

### Static Files
- `GET /static/widget/chatbot.html` - Widget HTML
- `GET /static/widget/chatbot.js` - Widget JavaScript
- `GET /static/widget/styles.css` - Widget CSS

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `True` |
| `SECRET_KEY` | Django secret key | Auto-generated |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `*` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `*` |
| `ANTHROPIC_API_KEY` | Anthropic API key | None |
| `OPENAI_API_KEY` | OpenAI API key | None |
| `AI_PROVIDER` | Default AI provider | `claude` |
| `BOT_NAME` | Bot display name | `Claude Assistant` |
| `BOT_POWERED_BY` | Powered by text | `Claude` |
| `BOT_COLOR` | Bot theme color | `#667eea` |
| `BOT_MSG_BG_COLOR` | Bot message bg color | `#667eea` |
| `BOT_ICON` | Bot icon URL | None |

## Development

### Running Tests

```bash
export DJANGO_SETTINGS_MODULE=config.settings.testing
python manage.py test
```

### Create Superuser

```bash
python manage.py createsuperuser
```

### Access Admin Panel

Navigate to `http://localhost:8000/admin`

## Key Features

### 1. Session Management
- UUID-based sessions with automatic cleanup
- JSON field storage for configuration and messages
- Last activity tracking with 30-minute timeout

### 2. AI Provider Support
- Singleton factory pattern for AI providers
- Runtime switching between Claude and OpenAI
- Unified response format

### 3. Context Building
- Token estimation and smart truncation
- CSV conversion for large data arrays
- File upload context integration
- Conversation history management

### 4. File Processing
- JSON and CSV file upload support
- Data type analysis and summarization
- Query capabilities for uploaded data
- 10MB file size limit

## Architecture Patterns

### Class-Based Views (CBV)
All API views use Django REST Framework's `APIView` for consistency:
- `SessionCreateView`, `SessionDetailView`
- `ChatMessageView`, `ChatHistoryView`
- `FileUploadView`, `FileInfoView`

### Service Layer
Business logic separated into service classes:
- `ChatService` - Context building and token management
- `AIProviderFactory` - AI provider management
- `FileProcessor` - File processing utilities

### Settings Split
Environment-specific settings:
- `base.py` - Common settings
- `development.py` - Dev overrides
- `production.py` - Production config
- `testing.py` - Test configuration

## Production Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Using Docker

```bash
docker build -t chatbot-widget-django .
docker run -p 8000:8000 --env-file .env chatbot-widget-django
```

### Environment Setup

```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
export DEBUG=False
export SECRET_KEY=<secure-random-key>
export ALLOWED_HOSTS=yourdomain.com
export DATABASE_URL=postgresql://user:pass@localhost/dbname
```

## Migration from Express.js

This Django backend is functionally equivalent to the Express.js backend with the following improvements:

1. **Database Storage**: Sessions stored in database instead of in-memory
2. **Settings Management**: django-environ for better configuration
3. **Class-Based Views**: More maintainable and reusable
4. **Admin Interface**: Built-in admin panel for session management
5. **ORM**: Django ORM for database operations
6. **Testing Framework**: Django test framework included

## Troubleshooting

### ModuleNotFoundError
Ensure `DJANGO_SETTINGS_MODULE` is set:
```bash
export DJANGO_SETTINGS_MODULE=config.settings.development
```

### CORS Issues
Update `ALLOWED_ORIGINS` in `.env`:
```env
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Database Locked
SQLite may lock in development. Use PostgreSQL for production.

## License

MIT
