# Phase 1: Core UI & Chat Loop (Next.js & FastAPI)

1.  **Project Foundation & Basic Layout (`apps/web`):**
    *   **Goal:** Establish the main application shell and theme capabilities.
    *   **Tasks:**
        *   Ensure Tailwind CSS is fully configured.
        *   Initialize `shadcn/ui` in your `apps/web` project (`npx shadcn-ui@latest init`). This will set up `globals.css` with CSS variables, `tailwind.config.js` helpers, and the `components.json` config.
        *   **Set up Root Layout (`apps/web/src/app/layout.tsx`):**
            *   Basic HTML structure.
            *   Integrate `next-themes`: Install it, wrap children with `<ThemeProvider attribute="class" defaultTheme="system" enableSystem>`.
            *   Define your initial light and dark mode color palettes using CSS variables in `apps/web/src/app/globals.css`. `shadcn/ui`'s init process helps with this.
        *   **Create Navbar Component (`apps/web/src/components/layout/navbar.tsx`):**
            *   Build the static navbar with placeholders for logo, brain icon, user avatar (using `shadcn/ui` components like `Button` for icons).
            *   Integrate this `Navbar` into `app/layout.tsx`.
        *   Create a basic **Chat Page (`apps/web/src/app/chat/page.tsx`):** For now, just a simple page that renders within the main layout to verify the shell.

2.  **Chat UI Components (`apps/web`):**
    *   **Goal:** Build the visual elements for the chat interface.
    *   **Tasks:** Using `shadcn/ui` (add components via CLI as needed):
        *   Create `components/chat/chat-input.tsx`: (e.g., `Input` and `Button` from `shadcn/ui`).
        *   Create `components/chat/message-list.tsx`: Container to display messages.
        *   Create `components/chat/message-item.tsx`: Component for individual message bubbles (differentiate user vs. assistant styles).
        *   Assemble these into `app/chat/page.tsx` to form the static chat UI.

3.  **Client-Side Chat Logic & TanStack Query (`apps/web`):**
    *   **Goal:** Make the chat UI interactive on the client-side and prepare for robust data handling.
    *   **Tasks:**
        *   Install `@tanstack/react-query`.
        *   Set up `QueryClient` and `QueryClientProvider` (e.g., in a client component that wraps your `app/layout.tsx` children, or more locally if preferred).
        *   In `app/chat/page.tsx` (or a custom hook):
            *   Manage local state for the current input field value (`useState`).
            *   Manage local state for the list of messages (`useState`).
            *   On send: Add the user's message to the local message list. *Initially, simulate an assistant response locally* (e.g., echo message, add a fixed reply after a delay) to test the UI updating.

4.  **FastAPI Backend - Basic Chat Endpoint (`apps/api`):**
    *   **Goal:** Create the backend service to handle chat requests.
    *   **Tasks:**
        *   Set up a new, minimal FastAPI project in your `apps/api/` directory.
        *   Create a `/chat` POST endpoint.
        *   This endpoint should:
            *   Receive a user message.
            *   (For now, you can have it return a simple, hardcoded streamed response or echo the message back).
            *   Later: This is where you'll integrate the OpenAI API call to get the actual LLM response and stream it.

5.  **Connect Frontend to Backend (`apps/web` & `apps/api`):**
    *   **Goal:** Establish the full end-to-end communication loop.
    *   **Tasks:**
        *   In `app/chat/page.tsx` (or your custom hook), replace the simulated assistant response:
            *   Use TanStack Query's `useMutation` hook to call your FastAPI `/chat` endpoint when a user sends a message.
            *   Handle the (streamed) response from FastAPI.
            *   Update the message list with the assistant's actual response.
        *   Ensure your FastAPI backend has CORS configured correctly to accept requests from your Next.js frontend.

---

## High-Level Next Steps Plan

### 1. Set Up State Management Foundations
**Goal:** Prepare the frontend for robust, scalable state handling.

- **a. Zustand (UI/Client State)**
  - Create a chat UI store (e.g., `features/chat/stores/chatUIStore.ts`).
    - Manages: input value, isThinking/loading, etc.
  - Wire up your chat input and UI to use Zustand for these states.

- **b. TanStack React Query (Server State)**
  - Install and set up QueryClientProvider at the app root.
  - Create chat-specific hooks (e.g., `features/chat/hooks/useChatMessages.ts`) for:
    - Fetching previous messages (useQuery)
    - Sending a new message (useMutation)

---

### 2. Connect Frontend to Backend (Core Chat Loop)
**Goal:** Make the chat actually talk to FastAPI.

- **a. FastAPI Endpoint**
  - Create a `/chat` POST endpoint that:
    - Receives a message (and thread ID, if you have threads)
    - (For now) Returns a simple echo or hardcoded response

- **b. Frontend Integration**
  - Update your send-message logic to use TanStack Query's mutation to call FastAPI.
  - On send:
    - Add the user's message to the UI (optimistic update)
    - Set `isThinking` to true (disable input, show spinner)
    - When response arrives, add AI's message to the UI, set `isThinking` to false, clear input

---

### 3. Modularize and Test Core Functionality
**Goal:** Ensure the basic chat loop works end-to-end.

- Test sending and receiving messages
- Test UI loading/disabled states
- Make sure the chat history displays correctly

---

### 4. Prepare for Persistence (Database)
**Goal:** Lay the groundwork for saving messages, but keep it simple for now.

- **a. FastAPI**
  - Plan for a database (e.g., Supabase, Postgres)
  - (Optional for now) Add stubs/placeholders for saving messages

- **b. Frontend**
  - Structure your code so that fetching/saving messages can be swapped from local state to server/database easily

---

### 5. Plan for Next Steps/Modularity
**Goal:** Make it easy to add features later.

- Keep Zustand and TanStack Query logic in `features/chat/` (feature-based structure)
- Use hooks and stores so you can add:
  - Streaming/multi-stage responses
  - Real-time updates
  - Message persistence/history
  - User authentication, etc.

---

## Summary Table

| Step | What to do | Where/How |
|------|------------|-----------|
| 1    | Set up Zustand for UI state | `features/chat/stores/chatUIStore.ts` |
| 2    | Set up TanStack Query for server state | `features/chat/hooks/useChatMessages.ts` + `QueryClientProvider` |
| 3    | Create FastAPI `/chat` endpoint | `apps/api/` |
| 4    | Connect send-message logic to FastAPI | Use mutation in React Query |
| 5    | Test core chat loop | UI: send, receive, loading |
| 6    | Plan for DB persistence | Add stubs, keep code modular |
| 7    | Modularize for future features | Feature-based folders, hooks, stores |

---

**This plan will let you:**
- Test the full chat loop (send, receive, loading)
- Have a clean, modular codebase
- Easily add database, streaming, and other features later

## Important Updates & Refinements

### Key Architecture Decisions

1. **Provider Organization**
   - Create dedicated `app/providers.tsx`
   - Combine all providers (QueryClientProvider, ThemeProvider, future providers)
   - Keeps `layout.tsx` clean and avoids prop-drilling

2. **Streaming First Approach**
   ```typescript
   // Frontend streaming setup
   const { mutateAsync } = useMutation({
     mutationFn: async (payload: ChatPayload) => {
       const res = await fetch('/api/chat', { /* ... */ });
       const reader = res.body!.getReader();
       const decoder = new TextDecoder();
       let done = false;
       while (!done) {
         const { value, done: d } = await reader.read();
         done = d;
         appendAssistantChunk(decoder.decode(value));
       }
     }
   });

   // FastAPI streaming setup
   from fastapi.responses import StreamingResponse
   def stream_llm(prompt):
       async def gen():
           for chunk in openai.chat.completions.create(..., stream=True):
               yield chunk.choices[0].delta.content or ""
       return StreamingResponse(gen(), media_type="text/plain")
   ```

3. **TypeScript Types Sharing**
   - Set up shared types between frontend and backend
   - Structure:
     ```
     packages/
       types/
         - message.ts
         - chat.ts
     ```

4. **CORS & Auth Setup**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### Revised Phase Approach

| Phase | Ship | Don't worry about yet |
|-------|------|----------------------|
| P0    | Streamed chat, loading states, light/dark theme toggles | DB persistence, auth |
| P1    | Save threads to DB, simple login | AI "memory" |
| P2    | Voice mode, RAG, knowledge graph UI | Fancy 3-pane layout, avatars |

### Development Best Practices
1. Use shadcn/ui CLI for component generation
2. Keep auto-fixing enabled (`pnpm dlx @next/cli lint --fix`)
3. Enable React-Query DevTools in dev layout
4. Implement streaming from day zero
5. Share TypeScript types between web & api
6. Keep Zustand minimal (only for UI state like sidebar collapse, theme toggle)

---

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
