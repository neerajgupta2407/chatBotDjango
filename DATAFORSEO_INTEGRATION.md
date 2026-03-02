# DataForSEO Integration

Integrates DataForSEO SEO data tools into the chatbot using AI tool/function calling. When users ask SEO-related questions, the AI automatically decides when to call DataForSEO APIs (SERP, Keywords, Backlinks, etc.) and incorporates the live data into its responses.

## How It Works

```
User: "What are the top results for 'python tutorial'?"
  → ChatMessageView builds messages + DataForSEO tool definitions
  → AI provider called with tools=[serp_google_organic_live, ...]
  → AI returns tool_call: serp_google_organic_live(keyword="python tutorial")
  → Backend executes tool via DataForSEOClient → calls DataForSEO REST API
  → Tool result (top 10 organic results) sent back to AI
  → AI generates natural language response with the SEO data
  → Response returned to user
```

The AI decides autonomously when to use tools — users just ask questions naturally.

## Setup

### 1. Get DataForSEO Credentials

Sign up at [https://dataforseo.com](https://dataforseo.com) and get your API credentials.

### 2. Configure Environment Variables

Add to your `.env` file:

```env
DATAFORSEO_USERNAME=your_email@example.com
DATAFORSEO_PASSWORD=your_api_password

# Optional: control which modules are enabled (default: all)
DATAFORSEO_ENABLED_MODULES=SERP,KEYWORDS_DATA,BACKLINKS,ONPAGE,DATAFORSEO_LABS

# Optional: max tool calls per message (default: 3)
DATAFORSEO_MAX_TOOL_CALLS=3
```

### 3. Run Migration

```bash
python manage.py migrate
```

### 4. Start the Server

```bash
python manage.py runserver
```

That's it. The integration is automatically active when credentials are set. If credentials are not configured, the chatbot works normally without SEO tools.

## Available Tools

### SERP Module

| Tool | Description | Key Parameters |
|------|-------------|---------------|
| `serp_google_organic_live` | Live Google organic search results | `keyword` (required), `location_name`, `language_name`, `device`, `depth` |

**Example questions:**
- "What are the top Google results for 'python tutorial'?"
- "Show me SERP results for 'best coffee maker' in the UK"
- "What ranks #1 for 'machine learning courses' on mobile?"

### KEYWORDS_DATA Module

| Tool | Description | Key Parameters |
|------|-------------|---------------|
| `kw_google_ads_search_volume` | Search volume for keywords | `keywords` (required, list), `location_name`, `language_name` |
| `kw_google_ads_keywords_for_site` | Keywords associated with a domain | `target` (required, domain), `location_name`, `language_name` |

**Example questions:**
- "What's the search volume for 'react vs vue'?"
- "What keywords does example.com rank for?"
- "Compare search volumes for 'python', 'javascript', and 'golang'"

### BACKLINKS Module

| Tool | Description | Key Parameters |
|------|-------------|---------------|
| `backlinks_summary` | Backlink profile summary | `target` (required, domain) |
| `backlinks_referring_domains` | List of referring domains | `target` (required), `limit` |

**Example questions:**
- "How many backlinks does example.com have?"
- "What's the domain authority of competitor.com?"
- "Show me the top referring domains for example.com"

### ONPAGE Module

| Tool | Description | Key Parameters |
|------|-------------|---------------|
| `onpage_instant_pages` | On-page SEO analysis | `url` (required, full URL) |

**Example questions:**
- "Analyze the SEO of https://example.com/blog/post"
- "What's the on-page score for this URL?"
- "Check the meta tags and page speed for https://example.com"

### DATAFORSEO_LABS Module

| Tool | Description | Key Parameters |
|------|-------------|---------------|
| `labs_google_keyword_ideas` | Keyword ideas from seed keywords | `keywords` (required, list), `location_name`, `language_name`, `limit` |
| `labs_google_domain_rank_overview` | Domain ranking overview | `target` (required, domain), `location_name`, `language_name` |

**Example questions:**
- "Give me keyword ideas related to 'digital marketing'"
- "What's the SEO overview for competitor.com?"
- "Suggest keywords related to 'cloud computing' and 'devops'"

## Configuration Levels

Tools can be configured at three levels (highest priority first):

### 1. Per-Session Config

Set `dataforseo_modules` in the session config when creating or updating a session:

```json
POST /api/chat/sessions/create
{
  "config": {
    "aiProvider": "claude",
    "dataforseo_modules": ["SERP", "KEYWORDS_DATA"]
  }
}
```

### 2. Per-Client Config

Set in the client's config JSON (via admin or API):

```json
{
  "dataforseo_modules": ["SERP", "BACKLINKS", "DATAFORSEO_LABS"]
}
```

### 3. Global (Environment Variable)

```env
DATAFORSEO_ENABLED_MODULES=SERP,KEYWORDS_DATA,BACKLINKS,ONPAGE,DATAFORSEO_LABS
```

### Disabling Tools

- **Disable globally:** Remove `DATAFORSEO_USERNAME` and `DATAFORSEO_PASSWORD` from `.env`
- **Disable per-client:** Set `"dataforseo_modules": []` in client config
- **Disable per-session:** Set `"dataforseo_modules": []` in session config

## Tool Call Loop

When the AI decides to use a tool, the backend executes a loop:

1. AI provider called with tool definitions
2. If AI returns `tool_calls`, each tool is executed via `DataForSEOClient`
3. Tool results are appended to the conversation
4. AI is called again with the results
5. Repeat until AI returns a text response (no more tool calls)
6. Maximum iterations controlled by `DATAFORSEO_MAX_TOOL_CALLS` (default: 3)

The AI may call multiple tools in one iteration (e.g., backlinks summary + keyword ideas) and chain tool calls across iterations.

## Architecture

### Files

```
config/settings/base.py              # DATAFORSEO_* settings
chat/services/dataforseo_tools.py    # Tool definitions (name, description, input_schema)
chat/services/dataforseo_client.py   # REST client (httpx, Basic Auth, result extraction)
chat/views/messages.py               # Tool call loop in ChatMessageView
chat/services/chat_service.py        # Tool messages in conversation history
chat/models/message.py               # "tool" role in ROLE_CHOICES
ai_providers/base.py                 # tools parameter in generate_response()
ai_providers/anthropic_provider.py   # Claude tool calling (tool_use content blocks)
ai_providers/openai_provider.py      # OpenAI function calling (tool_calls)
ai_providers/factory.py              # Passes tools through to providers
```

### Provider-Specific Handling

**Claude (Anthropic):**
- Tools passed as `tools` parameter directly (Anthropic format matches our schema)
- Responses with `tool_use` content blocks are parsed into normalized `tool_calls`
- Tool results sent as `user` messages with `tool_result` content blocks
- System messages extracted to separate `system` parameter when tools are active

**OpenAI:**
- Tools converted from our format to OpenAI function calling format (`type: "function"`)
- Responses with `message.tool_calls` parsed into normalized format
- Tool results sent as `role: "tool"` messages with `tool_call_id`

### Normalized Message Format

The view tracks messages in a provider-agnostic format:

```python
# Regular messages
{"role": "user", "content": "What are top results for python?"}
{"role": "assistant", "content": "Here are the results..."}

# Assistant requesting tool use
{
    "role": "assistant",
    "content": "Let me search for that.",
    "tool_calls": [
        {"id": "toolu_123", "name": "serp_google_organic_live", "input": {"keyword": "python"}}
    ]
}

# Tool result
{
    "role": "tool",
    "tool_call_id": "toolu_123",
    "name": "serp_google_organic_live",
    "content": "{\"keyword\": \"python\", \"organic_results\": [...]}"
}
```

Each provider converts this normalized format to its API-specific format internally.

## Testing

### Run DataForSEO Tests

```bash
export DJANGO_SETTINGS_MODULE=config.settings.testing

# All DataForSEO tests (80 tests)
python manage.py test chat.tests.test_dataforseo_tools chat.tests.test_dataforseo_client chat.tests.test_dataforseo_integration -v 2

# Individual test files
python manage.py test chat.tests.test_dataforseo_tools       # Tool definitions (21 tests)
python manage.py test chat.tests.test_dataforseo_client       # API client (28 tests)
python manage.py test chat.tests.test_dataforseo_integration  # Integration (31 tests)

# Full test suite (257 tests)
python manage.py test
```

### Manual Testing

```bash
# 1. Create a session
curl -X POST http://localhost:8000/api/chat/sessions/create \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cb_your_api_key" \
  -d '{"config": {"aiProvider": "claude"}, "user_identifier": "test@example.com"}'

# 2. Send an SEO question
curl -X POST http://localhost:8000/api/chat/messages/send \
  -H "Content-Type: application/json" \
  -H "X-API-Key: cb_your_api_key" \
  -d '{
    "sessionId": "SESSION_ID_FROM_STEP_1",
    "message": "What are the top organic results for python tutorial?"
  }'

# 3. Check logs for tool execution
# Look for: "DataForSEO tools enabled: 8 tools from modules [...]"
# Look for: "Tool call iteration 1: ['serp_google_organic_live']"
# Look for: "Tool calling completed after 1 iteration(s)"
```

## Cost Awareness

DataForSEO charges per API call. Each tool execution = 1 API call. The `DATAFORSEO_MAX_TOOL_CALLS` setting (default: 3) limits how many tool calls can happen per user message. Monitor your DataForSEO dashboard for usage.

**Tips to control costs:**
- Limit enabled modules to only what you need
- Set `DATAFORSEO_MAX_TOOL_CALLS=1` to restrict to single tool calls
- Use per-client config to enable tools only for specific clients
- Disable tools for demo/free-tier clients by setting `"dataforseo_modules": []`

## Graceful Degradation

- If `DATAFORSEO_USERNAME`/`DATAFORSEO_PASSWORD` are not set → tools are silently disabled, chatbot works normally
- If a DataForSEO API call fails → error is returned to the AI, which responds gracefully
- If max tool iterations are reached → AI responds with whatever data it has
- If an unknown tool name is encountered → error dict returned, AI handles it
