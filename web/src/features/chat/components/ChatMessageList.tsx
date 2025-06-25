"use client";

import React, { useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage'; 
import { Message } from '@/lib/types';

interface ChatMessageListProps {
  messages: Message[];
  fetchNextPage: () => void;
  hasNextPage?: boolean;
  isFetchingNextPage?: boolean;
}

const ChatMessageList: React.FC<ChatMessageListProps> = ({ messages, fetchNextPage, hasNextPage, isFetchingNextPage }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const el = e.currentTarget;
    if (el.scrollTop === 0 && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  };

  return (
    <div ref={scrollRef} onScroll={handleScroll} className="flex-grow overflow-y-auto p-4 space-y-2 bg-background">
      {messages.map((msg) => (
        <ChatMessage key={msg.id} message={msg} />
      ))}
      {messages.length === 0 && (
        <p className="text-sm text-muted-foreground text-center">No messages yet. Start the conversation!</p>
      )}
    </div>
  );
};

export default ChatMessageList; 