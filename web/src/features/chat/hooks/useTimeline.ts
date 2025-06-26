import { useInfiniteQuery } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase/supabase";
import { Message } from "@/lib/types";

const PAGE_SIZE = 20; // load bigger chunks for smoother scroll

interface DBRow {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  metadata?: { file_urls?: string[] } | null;
}

function dbRowToMessage(row: DBRow): Message {
  const meta = row.metadata;
  return {
    id: row.id,
    text: row.content,
    sender: row.role === "assistant" ? "ai" : "user",
    timestamp: row.created_at,
    files: Array.isArray(meta?.file_urls)
      ? meta!.file_urls!.map((url) => ({
          id: url,
          url,
          name: url.split("/").pop() ?? "file",
          size: 0,
          type: "image",
        }))
      : undefined,
  };
}

async function fetchPage(userId: string, before?: string) {
  let q = supabase
    .from("messages")
    .select(
      "id, role, content, created_at, metadata, conversations!inner(user_id)"
    )
    .eq("conversations.user_id", userId)
    .order("created_at", { ascending: false })
    .limit(PAGE_SIZE);

  if (before) q = q.lt("created_at", before);

  const { data, error } = await q;
  if (error) throw error;

  const rows = (data ?? []).reverse().map(dbRowToMessage);

  return {
    rows,
    nextCursor: rows.length === PAGE_SIZE ? rows[0].timestamp : undefined,
  };
}

export function useTimeline(userId?: string) {
  return useInfiniteQuery<{ rows: Message[]; nextCursor?: string }, Error>({
    queryKey: ["timeline", userId],
    enabled: !!userId,
    initialPageParam: undefined,
    queryFn: ({ pageParam }) => fetchPage(userId!, pageParam as string),
    getNextPageParam: (lastPage) => lastPage.nextCursor,
  });
} 