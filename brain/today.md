## 🗓️ Today – Ship *Persistent Chat History* (Supabase + React Query)

### 1  Goal
When a user reloads the chat page they immediately see the last **20** messages of today's conversation, can scroll up to load older messages, and automatically roll into yesterday's conversation when today is exhausted.  Optimistic-UI & the existing WebSocket streaming stay exactly as they are.

---
### 2  Step-by-step implementation (plain list)

1. **Ensure Row-Level Security** (Supabase Dashboard)
   • `conversations` and `messages` tables: add `user_id = auth.uid()` policy for `SELECT`.

2. **Create history hook** – `web/src/lib/hooks/useMessages.ts`
   • `useInfiniteQuery` + Supabase. First page: `LIMIT 20` newest rows.
   • Subsequent pages: `before=<oldest_created_at>`, again `LIMIT 20`.
   • Return `{ rows, nextCursor }`.

3. **Wire hook into chat logic** – edit `web/src/lib/hooks/useChat.ts`
   a. Call `useMessages(conversationId)` once `/api/chat/today` resolves.
   b. On success set `messages` state with the flattened pages.
   c. After every optimistic send / streamed chunk, also call
      `queryClient.setQueryData(['messages', conversationId], updater)` so cache stays current.

4. **Add scroll-up fetch** – edit `web/src/features/chat/components/ChatMessageList.tsx`
   • `onScroll` handler: when `scrollTop === 0` and `hasNextPage`, call `fetchNextPage()`.
   • Auto-scroll to bottom for new messages remains as is.

5. **Plumb paging props** – edit `ChatView.tsx`
   • Pass `{ fetchNextPage, hasNextPage, isFetchingNextPage }` from `useChat` down to the list.
   • Optional: render a "Loading older…" spinner.

6. **(Nice-to-have) Previous day rollover** – extend `useMessages.ts`
   • When `hasNextPage === false`, query Supabase for the previous `conversation_id` (`conv_day < today` order desc limit 1).
   • Update `conversationId` state to trigger the same history fetching for that day.

---
### 3  Key code snippets

```ts
// useMessages.ts (NEW)
export function useMessages(conversationId?: string) {
  return useInfiniteQuery({
    queryKey: ['messages', conversationId],
    enabled: !!conversationId,
    initialPageParam: undefined,            // first page
    queryFn: ({ pageParam }) => fetchPage(conversationId!, pageParam),
    getNextPageParam: last => last.nextCursor, // undefined = no more rows
  });
}

async function fetchPage(id: string, before?: string) {
  let q = supabase
    .from('messages')
    .select('id, role:role, content, created_at, message_metadata')
    .eq('conversation_id', id)
    .order('created_at', { ascending: false })
    .limit(20);
  if (before) q = q.lt('created_at', before);
  const { data, error } = await q;
  if (error) throw error;
  const rows = (data ?? []).reverse(); // oldest → newest
  return {
    rows,
    nextCursor: rows.length === 20 ? rows[0].created_at : undefined,
  };
}
```

---
### 4  Testing checklist
1. Refresh → last 20 messages appear instantly.
2. Send message → optimistic display, stays after refresh.
3. Scroll to top → older 20 messages prepend. Repeat.
4. After today's messages exhausted, list continues into yesterday.
5. Login with second user → cannot read first user's rows (RLS verifies).

---
Owner: **Frontend team** · Est. effort ⬩ 3–4 hrs for base paging, +2 hrs polish.
