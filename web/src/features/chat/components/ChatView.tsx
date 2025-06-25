"use client";

import React, { useRef, useLayoutEffect } from 'react';
import ChatMessageInput from './ChatMessageInput';
import ChatMessageList from './ChatMessageList';
import { useChat } from '@/features/chat/hooks/useChat';

// Later, we'll import MessageList and ChatInput here
// import MessageList from './MessageList';
// import ChatInput from './ChatInput';

interface ChatViewProps {
  conversationId?: string; // Make conversationId optional
}

export default function ChatView({ conversationId }: ChatViewProps) {
  // If conversationId is provided, use it, otherwise let useChat use its default "test"
  const { messages, isConnected, sendMessage, loading, isReconnecting, fetchNextPage, hasNextPage, isFetchingNextPage } = useChat(conversationId ? { conversationId } : {});
  
  // Debounce connection status to prevent flashing
  const [showDisconnected, setShowDisconnected] = React.useState(false);
  
  const outerRef = useRef<HTMLDivElement>(null);
  const prevHeightRef = useRef<number>(0);

  // auto-scroll logic
  useLayoutEffect(() => {
    const el = outerRef.current;
    if (!el) return;

    const initialLoad = prevHeightRef.current === 0;
    const wasAtBottom =
      el.scrollTop + el.clientHeight >= prevHeightRef.current - 10;

    if (initialLoad || wasAtBottom) {
      el.scrollTop = el.scrollHeight;
    }

    prevHeightRef.current = el.scrollHeight;
  }, [messages]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const el = e.currentTarget;
    if (el.scrollTop === 0 && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  };

  React.useEffect(() => {
    if (!isConnected && !loading && !isReconnecting) {
      // Show disconnected message after a short delay to avoid flashing during normal reconnection
      const timer = setTimeout(() => setShowDisconnected(true), 2000);
      return () => clearTimeout(timer);
    } else {
      setShowDisconnected(false);
    }
  }, [isConnected, loading, isReconnecting]);

  return (
    // Main container for the chat interface: full width to push scrollbar to edge
    <div className="flex flex-col h-full w-full">
      
      {/* Message display area */}
      <div className="flex-1 overflow-y-auto w-full pb-4" ref={outerRef} onScroll={handleScroll}>
        <div className="max-w-3xl mx-auto w-full p-4 sm:p-6 space-y-4">
          <ChatMessageList messages={messages} />
          {loading && (
            <p className="text-sm text-muted-foreground text-center">Loading conversation...</p>
          )}
          {isReconnecting && (
            <p className="text-sm text-muted-foreground text-center">Reconnecting...</p>
          )}
          {showDisconnected && (
            <p className="text-sm text-muted-foreground text-center">Connection lost. Please refresh if this persists.</p>
          )}
        </div>
      </div>

      {/* Input area */}
      <div className="w-full bg-background">
        <div className="max-w-3xl mx-auto">
          <ChatMessageInput onSendMessage={sendMessage} disabled={!isConnected} />
        </div>
      </div>
    </div>
  );
} 