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
│   │   ├── database.py          # Async DB connection with asyncpg
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
- Uses async database sessions with proper await patterns

```python
@router.websocket("/ws/chat/{conversation_id}")
async def websocket_chat_endpoint(websocket: WebSocket, conversation_id: str):
    async for db in get_async_db():
        try:
            # Authentication and connection handling
            # Delegates to handle_chat_message with async db session
            await handle_chat_message(
                user_id=authed_user_id,
                conversation_id=conversation_id,
                user_message=data,
                db=db,  # Pass async db session
                stream_callback=websocket.send_text
            )
        # Error handling and cleanup
```

#### Conversation Management (`conversation.py`)
- Provides REST endpoints for creating/retrieving conversations
- Handles timezone-aware "today" conversation creation
- Uses SQLAlchemy 2.0 style select() statements for async support
- Properly uses async/await patterns with database operations

```python
@router.get("/conversations/today")
async def get_or_create_today_conversation(
    tz: str = Query("UTC"),
    user_id: str = Depends(get_current_user_id_from_token),
    db: AsyncSession = Depends(get_async_db),
):
    # Use SQLAlchemy 2.0 style select
    stmt = select(Conversation).where(
        Conversation.user_id == user_id,
        Conversation.conv_day == today_local
    )
    result = await db.execute(stmt)
    convo = result.scalar_one_or_none()
    
    # Create new if not found
    if convo is None:
        # Create with async commit
        db.add(convo)
        await db.commit()
        await db.refresh(convo)
```

### 2. Service Layer (`app/services/`)

#### Chat Service (`chat_service.py`)
- Orchestrates the entire chat flow with async/await patterns:
  1. Saves user message to database using async SQLAlchemy
  2. Fetches conversation context with async calls
  3. Builds prompt for LLM
  4. Calls OpenAI asynchronously and streams response
  5. Saves AI response to database with async commits

```python
async def handle_chat_message(user_id, conversation_id, user_message, db: AsyncSession, stream_callback):
    # 1. Save user message with async SQLAlchemy
    user_msg = Message(
        conversation_id=conv_id_obj,
        user_id=user_id,
        role="user",
        content=user_message,
        message_metadata={}  # Use Python dict for JSONB
    )
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)
    
    # 2. Fetch context asynchronously
    context = await fetch_recent_messages(conversation_id, db)
    
    # 3-4. Build prompt and stream LLM response
    async for chunk in stream_chat_completion(prompt):
        # Stream chunks with timeout protection
        
    # 5. Save AI response asynchronously
    await db.commit()
```

#### Memory Service (`memory_service.py`)
- Retrieves recent messages from the database for context
- Uses SQLAlchemy 2.0 select() syntax for async compatibility
- Properly handles UUID types and ordering

```python
async def fetch_recent_messages(conversation_id: str, db: AsyncSession, limit: int = 10):
    # SQLAlchemy 2.0 style select for async compatibility
    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    
    # Execute asynchronously
    result = await db.execute(query)
    messages = result.scalars().all()
```

### 3. LLM Integration (`app/llm/`)

#### OpenAI Client (`openai_client.py`)
- Configures AsyncOpenAI client with timeouts
- Implements asynchronous streaming with proper error handling
- Yields response chunks as they arrive with async generators

```python
async def stream_chat_completion(messages: list[dict]) -> AsyncGenerator[str, None]:
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
        # Handle timeouts
        yield "\n\n[Error: The AI service took too long to respond...]"
```

### 4. Database Layer (`app/db/`)

#### Database Connection (`database.py`)
- Uses SQLAlchemy's async API with asyncpg driver
- Configured for Supabase's session pooler mode
- Proper connection pooling and error handling
- Async session factory with proper cleanup

```python
# Create an async engine with optimized settings
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,      # Verify connections before use
    pool_recycle=180,        # Drop idle connections after 3 minutes
    pool_size=10,            # Appropriate pool size
    max_overflow=5,          # Allow some overflow for peak loads
    echo=True,               # Log SQL queries
)

# Create async session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # Prevent loading expired attributes
)

# Async database session dependency
async def get_async_db():
    session = async_session_maker()
    try:
        yield session
    finally:
        await session.close()
```

#### Data Models (`models.py`)
- Defines SQLAlchemy ORM models with proper PostgreSQL types:
  - `Conversation`: Stores chat conversations with timezone support
  - `Message`: Stores individual chat messages with JSONB metadata
- Uses PostgreSQL's native UUID type for keys
- Includes indexes for query optimization

```python
class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    conversation_id = Column(UUID, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID, nullable=True) 
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    message_metadata = Column("metadata", JSONB, nullable=True)  # Explicitly JSONB type
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
```

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
- Support for versioned deployments and rollbacks

## Data Flow

1. **User sends message** → WebSocket endpoint receives it
2. **WebSocket handler** authenticates and passes to chat service with async DB session
3. **Chat service** asynchronously saves message and retrieves context
4. **Chat agent** builds LLM prompt with system instructions
5. **OpenAI client** calls API asynchronously with streaming and timeout protection
6. **Response chunks** are streamed back through WebSocket
7. **Complete response** is asynchronously saved to database

## Recent Optimizations

1. **Async Database Layer**:
   - Replaced thread pool executor pattern with true async/await using asyncpg
   - Uses SQLAlchemy 2.0 async API for all database operations
   - Fully non-blocking I/O for database operations

2. **Supabase Session Pooler Mode**:
   - Configured PostgreSQL to use "session" pooler mode instead of "transaction"
   - Allows for proper prepared statement handling with asyncpg
   - Maintains client-server connection throughout a session

3. **PostgreSQL Type Handling**:
   - Native UUID type support for primary and foreign keys
   - JSONB type for metadata with proper Python dict handling
   - Proper timezone-aware date/time handling

4. **Connection Management**:
   - Configurable connection pool size (currently 10)
   - `pool_pre_ping=True` to verify connections before use
   - `pool_recycle=180` to drop idle connections after 3 minutes
   - `expire_on_commit=False` to prevent loading expired attributes

5. **Timeout Protection**:
   - OpenAI client configured with 15s default timeout
   - Individual requests can specify custom timeouts (30s)
   - Graceful error handling for timeouts

6. **Health Check Optimization**:
   - Ultra-lightweight `/health` endpoint that responds quickly
   - Fly.io health check configuration with 30s grace period
   - Prevents false unhealthy status during startup

These optimizations ensure high scalability by leveraging async/await patterns throughout the stack, properly handling database connections for optimal performance, and maintaining robust error handling and timeout protection.
