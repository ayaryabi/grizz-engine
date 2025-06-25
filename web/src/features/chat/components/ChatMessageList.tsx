"use client";

import React from 'react';
import ChatMessage from './ChatMessage'; 
import { Message } from '@/lib/types';

interface ChatMessageListProps {
  messages: Message[];
}

const ChatMessageList: React.FC<ChatMessageListProps> = ({ messages }) => (
  <>
    {messages.map((msg) => (
      <ChatMessage key={msg.id} message={msg} />
    ))}
    {messages.length === 0 && (
      <p className="text-sm text-muted-foreground text-center">No messages yet. Start the conversation!</p>
    )}
  </>
);

export default ChatMessageList; 