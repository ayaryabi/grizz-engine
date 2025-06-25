import { Message } from "@/lib/types";

export function dedupMessages(messages: Message[]): Message[] {
  const map = new Map<string, Message>();
  for (const msg of messages) {
    map.set(msg.id, msg);
  }
  return Array.from(map.values()).sort(
    (a, b) => new Date(a.timestamp ?? 0).getTime() - new Date(b.timestamp ?? 0).getTime()
  );
} 