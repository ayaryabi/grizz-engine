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
