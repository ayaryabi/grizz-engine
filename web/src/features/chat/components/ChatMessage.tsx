"use client";

import React from 'react';
import { Message } from '@/lib/types';
import { cn } from "@/lib/utils";

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.sender === 'user';

  return (
    <div className={cn("flex mb-3", isUser ? "justify-end" : "justify-start")}>
      {isUser ? (
        <div className="max-w-[70%] text-sm leading-relaxed break-words px-4 py-2.5 rounded-xl shadow-sm bg-primary text-primary-foreground rounded-br-none">
          <p>{message.text}</p>
        </div>
      ) : (
        <p className="text-foreground max-w-[70%] text-sm leading-relaxed break-words">
          {message.text}
        </p>
      )}
    </div>
  );
};

export default ChatMessage; 