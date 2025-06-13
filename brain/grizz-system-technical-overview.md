# Grizz System Technical Overview

*Last Updated: January 2025*

## System Architecture Overview

The Grizz AI system is a real-time chat application built with a modern distributed architecture:

**Frontend**: Next.js 15 + React 19 with TypeScript
**Backend**: Python FastAPI with Redis job queue system
**Database**: PostgreSQL with SQLAlchemy ORM
**Real-time Communication**: WebSockets
**Authentication**: Supabase Auth + JWT tokens

```
┌─────────────────┐    WebSocket     ┌─────────────────┐    Redis Queue    ┌─────────────────┐
│   Next.js Web   │ ←──────────────→ │   FastAPI API   │ ←──────────────→ │  Python Workers │
│    Frontend     │                  │     Server      │                  │   (LLM Agents)  │
└─────────────────┘                  └─────────────────┘                  └─────────────────┘
        │                                      │                                      │
        │                                      │                                      │
        ▼                                      ▼                                      ▼
┌─────────────────┐                  ┌─────────────────┐                  ┌─────────────────┐
│   Supabase      │                  │   PostgreSQL    │                  │   OpenAI API    │
│   (Auth + File) │                  │   Database      │                  │   (GPT Models)  │
└─────────────────┘                  └─────────────────┘                  └─────────────────┘
```

## Core Tech Stack

### Frontend (Next.js)
- **Framework**: Next.js 15.3.1 with App Router
- **UI**: React 19 + Radix UI components + TailwindCSS
- **State Management**: Zustand for global state, React Query for server state
- **Auth**: Supabase Auth with JWT tokens
- **Real-time**: WebSocket connections to FastAPI
- **File Upload**: Direct to Supabase Storage

**Key Dependencies:**
```json
{
  "next": "15.3.1",
  "react": "^19.0.0",
  "@supabase/supabase-js": "^2.49.4",
  "@tanstack/react-query": "^5.76.1",
  "zustand": "^5.0.4",
  "react-markdown": "^10.1.0"
}
```

### Backend (Python FastAPI)
- **Framework**: FastAPI 0.109.2 with Uvicorn
- **Database**: PostgreSQL + SQLAlchemy (async) + Asyncpg
- **Queue System**: Redis Streams with Consumer Groups
- **LLM Integration**: OpenAI SDK + Agent SDK framework
- **Authentication**: JWT validation via Supabase
- **Monitoring**: Sentry for error tracking

**Key Dependencies:**
```python
fastapi==0.109.2
sqlalchemy==2.0.41
redis==6.1.0
openai==1.79.0
psycopg2-binary==2.9.10
```

## High-Level Message Flow

### 1. User Sends Message
```
User Types → React Component → useChat Hook → WebSocket → FastAPI → Redis Queue → Worker → OpenAI → Response Stream
```

### 2. Daily Conversation Creation
```
Frontend → /api/chat/today → Supabase Auth → FastAPI /api/conversations/today → PostgreSQL → Return Conversation ID
```

### 3. Real-time Response Streaming
```
OpenAI Streaming → Worker → Redis Results Stream → FastAPI WebSocket → Frontend → Real-time UI Update
```

## Frontend Architecture

### Directory Structure
```
web/src/
├── app/                    # Next.js App Router
│   ├── chat/page.tsx      # Main chat interface
│   ├── auth/page.tsx      # Authentication page
│   └── api/chat/today/    # API route for conversation creation
├── features/
│   ├── auth/              # Authentication components & context
│   └── chat/              # Chat-specific components
├── lib/
│   ├── hooks/useChat.ts   # Main WebSocket & chat logic
│   ├── types.ts           # TypeScript definitions
│   └── supabase/          # Supabase client configuration
└── components/ui/         # Reusable UI components
```

### Key Frontend Components

**1. ChatView Component (`ChatView.tsx`)**
- Main chat interface container
- Handles connection status display
- Manages message list and input components

**2. useChat Hook (`useChat.ts`)**
- WebSocket connection management
- Message state management
- Automatic reconnection with exponential backoff
- File upload handling
- Heartbeat/ping system for connection health

**3. Daily Conversation Logic**
- Fetches today's conversation ID on app load
- Creates new conversation per day per user
- Timezone-aware conversation grouping
- Caches conversation ID in localStorage

### Authentication Flow
```
1. User visits site → Redirected to auth page
2. Magic link authentication via Supabase
3. JWT token stored in session
4. Token passed in WebSocket connection
5. Backend validates token with Supabase
```

## Backend Architecture

### Directory Structure
```
ai-engine/
├── main.py                    # FastAPI app entry point
├── launcher.py               # Process manager (API + Workers)
├── app/
│   ├── api/
│   │   ├── ws.py            # WebSocket handlers
│   │   └── conversation.py  # Conversation management
│   ├── workers/
│   │   └── llm_worker.py    # Job processing workers
│   ├── agents/
│   │   ├── chat_agent.py    # Grizz personality agent
│   │   └── memory/          # Memory management system
│   ├── core/
│   │   ├── queue.py         # Redis queue operations
│   │   ├── redis_client.py  # Redis connection management
│   │   └── auth.py          # JWT authentication
│   ├── db/
│   │   ├── models.py        # SQLAlchemy models
│   │   └── database.py      # Database configuration
│   └── services/
│       └── queue_service.py # High-level queue operations
├── logs/                     # Worker and API logs
└── requirements.txt
```

### Core Backend Components

**1. FastAPI Application (`main.py`)**
- CORS configuration for frontend communication
- Health check endpoints
- Database initialization
- Redis connection pool setup
- Sentry error monitoring

**2. WebSocket Handler (`ws.py`)**
- Real-time chat communication
- JWT token validation
- Message persistence to database
- Job queuing for LLM processing
- Result streaming to clients
- Connection lifecycle management (idle timeout, reconnection)

**3. Redis Queue System (`queue.py`, `queue_service.py`)**
- **Job Queuing**: User messages → Redis Streams
- **Consumer Groups**: Multiple workers process jobs
- **Backpressure Detection**: Prevents system overload
- **Result Publishing**: Streams LLM responses back to clients
- **Dead Letter Queue**: Failed job handling

**4. LLM Workers (`llm_worker.py`)**
- Process jobs from Redis queue
- Conversation context fetching
- OpenAI API integration via Agent SDK
- Response streaming via Redis
- Error handling and retry logic
- Database persistence of complete responses

**5. Chat Agent (`chat_agent.py`)**
- **Grizz Personality**: Full character instructions
- **Tool Integration**: Web search, memory management
- **Agent SDK**: Structured LLM interaction framework
- **Streaming Support**: Real-time response generation

## Database Schema

### PostgreSQL Tables

**Conversations Table:**
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    title VARCHAR(100) DEFAULT 'New Conversation',
    conv_day DATE NOT NULL,           -- User's local date
    user_tz VARCHAR NOT NULL DEFAULT 'UTC',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, conv_day)         -- One conversation per user per day
);
```

**Messages Table:**
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID,
    role VARCHAR(20) NOT NULL,        -- 'user' or 'assistant'
    content TEXT NOT NULL,
    metadata JSONB,                   -- File URLs, processing info
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Memory Table:**
```sql
CREATE TABLE memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    item_type TEXT DEFAULT 'note',
    title TEXT,
    content TEXT,
    properties JSONB DEFAULT '{}',
    file_url TEXT,
    mime_type TEXT,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Redis Architecture

### Stream-Based Job Queue
```
Stream: llm_jobs
├── Job Data: {job_id, user_id, conversation_id, message, metadata}
├── Consumer Group: "llm_workers"
├── Workers: worker-0, worker-1, worker-2...
└── Dead Letter: llm_jobs_dead
```

### Result Streaming
```
Stream: llm_results
├── Result Data: {job_id, client_id, chunk, is_final}
├── Client Filtering: Each WebSocket client gets own results
└── Auto-cleanup: Streams trimmed periodically
```

### Key Features
- **Consumer Groups**: Ensure exactly-once job processing
- **Backpressure**: Prevents system overload (5000 job limit)
- **Long Polling**: Reduces Redis operations (15s blocks)
- **Connection Pooling**: Optimized Redis connections
- **Stream Maintenance**: Automatic cleanup tasks

## Process Management

### Multi-Process Architecture
```
launcher.py
├── FastAPI Web Server (uvicorn)
├── Worker-0 (Python process)
├── Worker-1 (Python process)
└── Worker-N (Python process)
```

### Features
- **Automatic Restart**: Failed processes restart automatically
- **Graceful Shutdown**: Proper cleanup on termination
- **Log Management**: Separate log files per process
- **Health Monitoring**: Process state monitoring

## Real-Time Communication

### WebSocket Flow
```
1. Frontend connects: ws://backend/ws/chat/{conversation_id}?token=jwt
2. Backend validates JWT with Supabase
3. Connection accepted, unique client_id assigned
4. User message received → saved to DB → queued for processing
5. Worker processes job → streams results to Redis
6. Backend listens for results → forwards to WebSocket client
7. Frontend receives chunks → updates UI in real-time
```

### Connection Management
- **Heartbeat System**: 4-minute ping intervals
- **Idle Timeout**: 5-minute server-side timeout
- **Reconnection**: Exponential backoff (1s → 30s max)
- **Tab Management**: Pauses heartbeat on inactive tabs
- **Error Recovery**: Graceful handling of network issues

## Grizz AI Personality

### Character Implementation
The Grizz personality is implemented through a comprehensive system prompt in `chat_agent.py`:

**Core Traits:**
- Friendly, caring bear companion for Gen Z users
- Emotionally intelligent with appropriate humor
- Uses bear metaphors and casual, modern language
- Provides honest guidance while being supportive
- Maintains consistent character across all interactions

**Capabilities:**
- **Web Search**: Current information retrieval
- **Memory System**: Personal detail retention
- **Image Analysis**: Visual content understanding
- **Emotional Support**: Context-aware responses

### Agent SDK Integration
```python
# Streaming response generation
streamed_result = Runner.run_streamed(chat_agent, conversation_input, context=message_context)

# Process streaming events
async for event in streamed_result.stream_events():
    if event.type == "raw_response_event":
        yield event.data.delta
```

## Performance Optimizations

### Frontend
- **React Query**: Intelligent caching and background updates
- **Optimistic Updates**: Immediate UI feedback
- **Conversation Caching**: localStorage for daily conversations
- **WebSocket Pooling**: Single connection per conversation
- **File Upload**: Direct to Supabase (bypasses backend)

### Backend
- **Async Operations**: Non-blocking database and Redis operations
- **Connection Pooling**: Optimized Redis and PostgreSQL connections
- **Stream Processing**: Efficient Redis stream operations
- **Long Polling**: Reduced Redis query frequency
- **Consumer Groups**: Parallel job processing

### Redis Optimizations
- **Blocking Reads**: 15-second blocks reduce polling
- **Stream Trimming**: Automatic cleanup prevents memory growth
- **Connection Reuse**: Pooled connections across workers
- **Batch Operations**: Process multiple results simultaneously

## Error Handling & Monitoring

### Sentry Integration
- **Error Tracking**: Comprehensive error capture across frontend/backend
- **Performance Monitoring**: Request/response timing
- **User Context**: Associated errors with user sessions
- **Custom Tags**: Conversation and job tracking

### Logging Strategy
```
Frontend: Console logging + Sentry for errors
Backend: Structured logging + Sentry integration
Workers: Separate log files per worker process
Redis: Operation-level error tracking
```

### Resilience Features
- **Automatic Retries**: Failed jobs retry up to 3 times
- **Dead Letter Queue**: Permanently failed jobs for analysis
- **Circuit Breakers**: Backpressure prevents overload
- **Graceful Degradation**: System continues with reduced functionality

## Deployment Architecture

### Current Setup
- **Backend**: Single instance with multiple worker processes
- **Frontend**: Static deployment (Vercel/Netlify style)
- **Database**: Managed PostgreSQL
- **Redis**: Managed Redis instance
- **File Storage**: Supabase Storage

### Scaling Considerations
- **Horizontal Scaling**: Add more worker processes
- **Load Balancing**: Multiple FastAPI instances
- **Database Scaling**: Read replicas for heavy read operations
- **Redis Scaling**: Redis Cluster for high throughput

## Security Model

### Authentication
- **JWT Tokens**: Supabase-issued tokens for API access
- **Token Validation**: Backend validates tokens with Supabase
- **Session Management**: Frontend handles token refresh
- **WebSocket Auth**: Token-based WebSocket connections

### Data Protection
- **CORS Configuration**: Restricted origins for API access
- **SQL Injection**: SQLAlchemy ORM prevents injection attacks
- **File Upload**: Validated file types and size limits
- **Rate Limiting**: Backpressure system prevents abuse

## Key Configuration

### Environment Variables
```bash
# Backend
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...
SENTRY_DSN=https://...

# Frontend
NEXT_PUBLIC_SUPABASE_URL=https://...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
NEXT_PUBLIC_FASTAPI_BACKEND_URL=http://...
```

### Scaling Parameters
```python
# Redis Queue
MAX_PENDING_JOBS = 5000
RATE_LIMIT_THRESHOLD = 3000
MAX_RETRY_COUNT = 3

# Worker Configuration
WORKER_COUNT = 2  # Configurable via launcher
CONSUMER_GROUP = "llm_workers"

# Connection Limits
REDIS_MAX_CONNECTIONS = worker_count * 2 + 10
```

## Development Workflow

### Local Development
```bash
# Frontend
cd web && npm run dev

# Backend
cd ai-engine && python launcher.py --workers 2
```

### Testing Strategy
- **Frontend**: React Testing Library + Jest
- **Backend**: Pytest for API and worker tests
- **Integration**: End-to-end WebSocket testing
- **Load Testing**: Redis queue performance under load

## Future Architecture Considerations

### Optimization Opportunities
1. **Redis Pub/Sub**: Replace polling with push notifications
2. **Caching Layer**: Add Redis caching for conversation history
3. **CDN Integration**: Static asset optimization
4. **Database Sharding**: User-based data distribution

### Monitoring Enhancements
1. **Metrics Dashboard**: Real-time system health monitoring
2. **Queue Analytics**: Job processing performance tracking
3. **User Analytics**: Conversation engagement metrics
4. **Cost Monitoring**: OpenAI API usage tracking

This technical overview provides a comprehensive understanding of the Grizz system architecture, enabling effective development planning and troubleshooting. The system is designed for real-time performance, scalability, and maintainability while delivering a premium AI chat experience.