"use client";

import React from 'react';
import ChatMessageInput from './ChatMessageInput';
import ChatMessageList from './ChatMessageList';
import { useChat } from '@/lib/hooks/useChat';

// Later, we'll import MessageList and ChatInput here
// import MessageList from './MessageList';
// import ChatInput from './ChatInput';

interface ChatViewProps {
  conversationId?: string; // Make conversationId optional
}

export default function ChatView({ conversationId }: ChatViewProps) {
  // If conversationId is provided, use it, otherwise let useChat use its default "test"
  const { messages, isConnected, sendMessage } = useChat(conversationId ? { conversationId } : {});

  return (
    // Main container for the chat interface: full width to push scrollbar to edge
    <div className="flex flex-col h-full w-full">
      
      {/* Message display area */}
      <div className="flex-1 overflow-y-auto w-full pb-4">
        <div className="max-w-3xl mx-auto w-full p-4 sm:p-6 space-y-4">
          <ChatMessageList messages={messages} />
          {!isConnected && (
            <p className="text-sm text-muted-foreground text-center">Connecting to chat server...</p>
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