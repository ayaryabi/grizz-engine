# Grizz AI Engine Codebase Overview

## Folder Structure

```
ai-engine/
├── app/                         # Core application code
│   ├── agents/                  # AI agent implementation
│   │   └── chat_agent.py        # Builds LLM prompts for chat
│   ├── api/                     # API endpoints
│   │   ├── conversation.py      # Conversation management endpoints
│   │   └── ws.py                # WebSocket implementation for chat
│   ├── core/                    # Core functionality
│   │   ├── auth.py              # JWT auth with Supabase integration
│   │   └── config.py            # App configuration and env vars
│   ├── db/                      # Database related code
│   │   ├── database.py          # DB connection with thread pooling
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   └── __init__.py
│   ├── llm/                     # Language model integration
│   │   └── openai_client.py     # OpenAI API client with timeout handling
│   ├── services/                # Business logic layer
│   │   ├── chat_service.py      # Chat message handling
│   │   └── memory_service.py    # Conversation history retrieval
│   └── main.py                  # FastAPI app initialization
├── requirements.txt             # Python dependencies
├── fly.toml                     # Fly.io deployment configuration
├── Dockerfile                   # Container definition
├── main.py                      # Entry point (redirects to app.main)
└── README.md                    # Project documentation
```

## Technical Architecture Overview

The Grizz AI Engine is built with a clean, modular architecture following the separation of concerns principle. Here's how the components work together:

### 1. API Layer (`app/api/`)

#### WebSocket Implementation (`ws.py`)
- Handles WebSocket connections for real-time chat
- Authenticates users via JWT tokens in query parameters
- Manages connection lifecycle (accept, receive, send, close)
- Delegates message handling to the service layer

```python
@router.websocket("/ws/chat/{conversation_id}")
async def websocket_chat_endpoint(websocket: WebSocket, conversation_id: str):
    # Authentication, connection handling, and message processing
    # Delegates actual chat processing to handle_chat_message
```

#### Conversation Management (`conversation.py`)
- Provides REST endpoints for creating/retrieving conversations
- Handles timezone-aware "today" conversation creation
- Integrates with database models

### 2. Service Layer (`app/services/`)

#### Chat Service (`chat_service.py`)
- Orchestrates the entire chat flow:
  1. Saves user message to database
  2. Fetches conversation context
  3. Builds prompt for LLM
  4. Calls OpenAI and streams response
  5. Saves AI response to database

```python
async def handle_chat_message(user_id, conversation_id, user_message, db, stream_callback):
    # 1. Save user message
    # 2. Fetch context from memory_service
    # 3. Build prompt with chat_agent
    # 4. Stream response from OpenAI with timeouts
    # 5. Save AI response
```

#### Memory Service (`memory_service.py`)
- Retrieves recent messages from the database for context
- Simple implementation with potential for more advanced features

### 3. LLM Integration (`app/llm/`)

#### OpenAI Client (`openai_client.py`)
- Configures AsyncOpenAI client with timeouts
- Implements streaming with proper error handling
- Yields response chunks as they arrive

```python
async def stream_chat_completion(messages):
    try:
        # Create request with timeout protection
        response = await client.chat.completions.create(
            model="gpt-4.1-2025-04-14",
            messages=messages,
            stream=True,
            timeout=30.0,  # Prevents blocking for too long
        )
        
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except asyncio.TimeoutError:
        # Proper timeout handling
        yield "\n\n[Error: The AI service took too long to respond...]"
```

### 4. Database Layer (`app/db/`)

#### Database Connection (`database.py`)
- Configures SQLAlchemy with optimized settings
- Implements thread pool executor pattern for non-blocking DB operations
- Includes connection recycling and verification

```python
# Create a synchronous engine with optimized settings
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,      # Verify connections before using
    pool_recycle=180,        # Drop idle connections after 3 minutes
    echo=True,
)

# Thread pool for non-blocking database operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

async def run_database_operation(operation_func, *args, **kwargs):
    """Run sync DB operations in a thread pool without blocking the event loop"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        thread_pool, 
        lambda: operation_func(*args, **kwargs)
    )
```

#### Data Models (`models.py`)
- Defines SQLAlchemy ORM models:
  - `Conversation`: Stores chat conversations with timezone support
  - `Message`: Stores individual chat messages
- Includes indexes for query optimization

### 5. Agent Layer (`app/agents/`)

#### Chat Agent (`chat_agent.py`)
- Builds prompts for the OpenAI LLM
- Contains Grizz's persona and behavior system prompt
- Combines context with new user messages

### 6. Core Infrastructure (`app/core/`)

#### Authentication (`auth.py`)
- JWT token validation with Supabase integration
- Token extraction from different sources (header, query params)
- Security checks (expiration, audience, issuer)

#### Configuration (`config.py`)
- Environment variable management
- Application settings

### 7. Deployment Configuration

#### Docker Configuration (`Dockerfile`)
- Multi-stage build for efficiency
- Python 3.13.3 base
- Virtual environment setup

#### Fly.io Configuration (`fly.toml`)
- Deployment settings for Fly.io
- Optimized health check configuration (30s grace period)
- Resource allocation (1GB memory)

## Data Flow

1. **User sends message** → WebSocket endpoint receives it
2. **WebSocket handler** authenticates and passes to chat service
3. **Chat service** saves message and retrieves context
4. **Chat agent** builds LLM prompt with system instructions
5. **OpenAI client** calls API with streaming and timeout protection
6. **Response chunks** are streamed back through WebSocket
7. **Complete response** is saved to database

## Recent Optimizations

1. **Async Non-Blocking Architecture**:
   - Thread pool executor pattern for database operations
   - Prevents blocking the main event loop during DB operations

2. **Connection Management**:
   - `pool_pre_ping=True` to verify connections before use
   - `pool_recycle=180` to drop idle connections after 3 minutes
   - Prevents "stale connection" errors

3. **Timeout Protection**:
   - OpenAI client configured with 15s default timeout
   - Individual requests can specify custom timeouts (30s)
   - Graceful error handling for timeouts

4. **Health Check Optimization**:
   - Ultra-lightweight `/health` endpoint that responds quickly
   - Fly.io health check configuration with 30s grace period
   - Prevents false unhealthy status during startup

These optimizations ensure the system doesn't hang during API calls, prevents cascading failures, and maintains high availability.
