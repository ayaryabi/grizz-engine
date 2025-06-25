import { useInfiniteQuery } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase/supabase";
import { Message } from "@/lib/types";

const PAGE_SIZE = 20;

interface DBRow {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  metadata?: Record<string, unknown>;
}

interface Page {
  rows: Message[];
  nextCursor?: string;
}

function dbRowToMessage(row: DBRow): Message {
  return {
    id: row.id,
    text: row.content,
    sender: row.role === "assistant" ? "ai" : "user",
    timestamp: row.created_at,
    files: Array.isArray((row.metadata as any)?.file_urls)
      ? (row.metadata as any).file_urls.map((url: string) => ({
          id: url,
          url,
          name: url.split("/").pop() ?? "file",
          size: 0,
          type: "image",
        }))
      : undefined,
  };
}

async function fetchPage(conversationId: string, before?: string): Promise<Page> {
  let q = supabase
    .from("messages")
    .select("id, role, content, created_at, metadata")
    .eq("conversation_id", conversationId)
    .order("created_at", { ascending: false })
    .limit(PAGE_SIZE);

  if (before) {
    q = q.lt("created_at", before);
  }

  const { data, error } = await q;
  if (error) throw error;

  const rows = (data ?? []) as DBRow[];
  const messageRows = rows.reverse().map(dbRowToMessage); // oldest → newest

  return {
    rows: messageRows,
    nextCursor:
      messageRows.length === PAGE_SIZE ? messageRows[0].timestamp : undefined,
  };
}

export function useMessages(conversationId?: string) {
  return useInfiniteQuery<Page, Error>({
    queryKey: ["messages", conversationId],
    enabled: !!conversationId,
    initialPageParam: undefined,
    queryFn: ({ pageParam }) =>
      fetchPage(conversationId!, pageParam as string | undefined),
    getNextPageParam: (lastPage) => lastPage.nextCursor,
  });
} 