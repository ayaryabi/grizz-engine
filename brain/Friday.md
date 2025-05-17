# Grizz Chat MVP – End-to-End System Flow (Detailed High-Level Summary)

## Frontend (Next.js)

1. **User Interface**
   - User types a message in the chat UI.
   - The message is immediately shown in the UI (optimistic update).

2. **Sending the Message**
   - The frontend sends the message (with user ID, conversation ID) to the backend via a **WebSocket** connection.
   - (For initial page load, React Query fetches previous messages from the backend using HTTP.)

3. **Receiving AI Responses**
   - As the backend generates the AI response, it streams each chunk/token back to the frontend over the WebSocket.
   - The UI displays the AI's response in real time, word-by-word or chunk-by-chunk.
   - **Markdown rendering** (e.g., with `react-markdown`) is used to display formatted AI output (bullet points, tables, code, etc.).

---

## Backend (FastAPI, Python)

1. **WebSocket Endpoint**
   - The backend exposes a `/ws/chat/{conversation_id}` WebSocket endpoint (in `api/ws.py`).
   - Receives messages from the frontend.

2. **Processing the Message**
   - **Authentication:** Verifies the user (API key, JWT, etc.).
   - **Database Save:** Saves the user's message to the database (`db/models.py`).
   - **Context Fetch:** Retrieves the last N messages for context (via `services/memory_service.py`).
   - **Prompt Construction:** Builds the prompt (system prompt + context + new message).
   - **LLM Call:** Sends the prompt to OpenAI (or other LLM) via `llm/openai_client.py` and streams the response.

3. **Streaming the Response**
   - As the LLM generates output, each chunk is:
     - **Published to a Redis Stream** (event bus) for durability and scalability.
     - **Read by the WebSocket handler** and sent to the frontend in real time.
   - **Database Save:** The AI's response is also saved as a new message in the database.

4. **(Optional, Future)**
   - The same WebSocket/Redis event system can be used to stream "thinking"/progress updates, tool calls, or multi-step agent progress to the frontend.

---

## Database (Postgres, etc.)

- Stores all users, conversations, messages, steps, and usage/cost data.
- Ensures all chat history and context is persistent and queryable.

---

## Redis (Event Bus)

- **Purpose:**  
  Acts as a real-time event bus for streaming data between backend processes and the frontend.
  Ensures that even if you scale to multiple backend servers, all events (LLM chunks, progress updates) are reliably delivered to the right user.
- **How:**  
  Backend writes each LLM chunk (or progress event) to a Redis Stream.
  WebSocket handler reads from the stream and pushes updates to the frontend.
  If a user disconnects and reconnects, missed events can be replayed from Redis.

---

## Frontend Message Display

- **React Query:**  
  Fetches and displays previous messages (chat history) on page load.
- **WebSocket:**  
  Receives and displays new, streaming messages in real time.
- **Markdown Renderer:**  
  Renders AI responses with formatting (bullet points, tables, code, etc.).

---

## Summary Table

| Step | What happens? | Where (file/folder) | Tech |
|------|---------------|---------------------|------|
| 1    | User sends message | `web/components/ChatView.tsx` | Next.js, WebSocket |
| 2    | Backend receives message | `ai-engine/app/api/ws.py` | FastAPI, WebSocket |
| 3    | Auth & save to DB | `app/core/security.py`, `db/models.py` | FastAPI, SQLAlchemy |
| 4    | Fetch context | `services/memory_service.py` | FastAPI, SQLAlchemy |
| 5    | Build prompt & call LLM | `agents/chat_agent.py`, `llm/openai_client.py` | FastAPI, OpenAI API |
| 6    | Stream response via Redis | `core/events.py` | Redis Streams |
| 7    | WebSocket sends to UI | `api/ws.py` | FastAPI, WebSocket |
| 8    | UI displays streaming response | `web/components/ChatView.tsx` | Next.js, react-markdown |
| 9    | Save AI response to DB | `db/models.py` | FastAPI, SQLAlchemy |

---

## Key Points

- **All messages (user & AI) are saved in the backend database.**
- **Redis is used for real-time, reliable event streaming between backend and frontend.**
- **WebSocket is the main channel for streaming new messages and progress to the UI.**
- **React Query is used for fetching and displaying chat history.**
- **Markdown rendering ensures AI responses look great in the UI.**
- **The architecture is modular and future-proof—easy to add tools, multi-agent, or more advanced features later.**

---

## MVP Polish & Edge Cases (Feedback Integration)

### Edge Cases to Pre-Plan

1. **Multiple Browser Tabs for the Same Conversation**
   - If a user opens the same chat in multiple tabs, sync state/messages between tabs using the BroadcastChannel API, or ensure only one Redis consumer per user/convo group on the backend. (MVP can start with one tab, but architect for this.)

2. **Back-pressure When User Hammers Enter**
   - Queue messages per conversation and process sequentially on the backend to avoid overlapping LLM calls and OpenAI rate limits. Optionally debounce/rate-limit on the frontend.

### Naming Tweaks
- Rename `api/ws.py` to `api/ws/chat.py` to avoid a dumping ground file and keep endpoints feature-based.
- Use `extra` or `meta` instead of `metadata` for the JSONB column in the `messages` table to avoid confusion with Postgres reserved words.

### Redis Stream Retention
- Set a max length or TTL (e.g., 24h or 7d) for Redis Streams to avoid unbounded memory growth. Add this to the Redis event publishing logic.

### Additional Best Practices
- Add SSE fallback for streaming so locked-down networks still see chunks.
- Rollback optimistic UI bubbles if the backend returns a 4xx error.
- Cap total tokens before LLM call; log a warning when context trim triggers.
- Put `usage_cents` on the row the moment chunks finish, so billing never lags.
- Decide how long to keep Redis stream entries to avoid unbounded memory.
- Use `rehype-highlight` for code blocks in markdown rendering for syntax colors.
- Add rate-limit middleware call in the flow doc so it's baked in, not an after-thought.

---
