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
