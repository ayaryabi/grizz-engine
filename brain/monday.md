# Monday Plan – Modular Chat Pipeline Next Steps

## 1. Create a `services/` Folder
- **Purpose:** Hold business logic that orchestrates chat, context, and LLM calls.

---

## 2. Implement `services/chat_service.py`
- **What it does:**
  - Receives a user message (from the WebSocket handler).
  - Saves the user message to the database.
  - Fetches recent context (last N messages) for the conversation.
  - Builds the prompt for the LLM.
  - Calls the LLM and streams the response back to the UI.
  - Saves the AI response to the database.

---

## 3. Implement `services/memory_service.py`
- **What it does:**
  - Fetches the last N messages for a given conversation from the database.
  - (Optional: In the future, can add summarization or advanced context logic.)

---

## 4. (Optional, but recommended) Implement `agents/chat_agent.py`
- **What it does:**
  - Builds the LLM prompt from the system prompt, context, and user message.
  - (Optional: In the future, can add multi-agent logic, tool use, etc.)

---

## 5. Refactor `api/ws.py` (WebSocket Handler)
- **What to change:**
  - Keep only connection/auth/streaming logic in this file.
  - When a message is received, call `chat_service.handle_chat_message(...)`.
  - Pass a callback (e.g., `websocket.send_text`) for streaming the LLM response.

---

## 6. Ensure `llm/openai_client.py` is Streaming-Ready
- **What to check:**
  - The LLM client should support streaming responses (yielding chunks).
  - Should be easy to swap out for other LLMs or add Redis streaming later.

---

## 7. Database Models (`db/models.py`)
- **What to check:**
  - You have models for `Message` and `Conversation`.
  - Each message has: `id`, `conversation_id`, `user_id`, `role` (user/ai), `content`, `created_at`.

---

## 8. Wire It All Together
- **Flow:**
  1. **Frontend** sends message via WebSocket.
  2. **`api/ws.py`** receives message, authenticates, calls `chat_service.handle_chat_message`.
  3. **`chat_service.py`** saves user message, fetches context (via `memory_service.py`), builds prompt (via `chat_agent.py`), calls LLM, streams response, saves AI message.
  4. **Frontend** receives streamed AI response.

---

## Why This Structure?
- **Easy to test:** Each part can be tested in isolation.
- **Easy to extend:** Add Redis, multi-agent, or new tools later with minimal refactor.
- **Separation of concerns:** API, business logic, LLM, and DB are all cleanly separated.

---

## Summary Table

| Step | File/Folder                | What to Implement/Check                        |
|------|----------------------------|------------------------------------------------|
| 1    | `services/`                | Create folder                                  |
| 2    | `services/chat_service.py` | Orchestrate chat pipeline                      |
| 3    | `services/memory_service.py`| Fetch last N messages for context              |
| 4    | `agents/chat_agent.py`     | Build LLM prompt (optional, but recommended)   |
| 5    | `api/ws.py`                | Refactor to call chat_service, keep thin       |
| 6    | `llm/openai_client.py`     | Ensure streaming support                       |
| 7    | `db/models.py`             | Ensure Message/Conversation models are solid   |
| 8    | (All)                      | Wire together for end-to-end chat flow         |

---

**This plan sets you up for a modular, scalable, and future-proof chat system.** 