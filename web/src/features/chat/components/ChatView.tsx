"use client"; // If it manages state or uses hooks like useState for messages later

import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import ChatMessageInput from './ChatMessageInput';
import { Message } from '@/lib/types';
import { v4 as uuidv4 } from 'uuid';
import ChatMessage from './ChatMessage';

// Later, we'll import MessageList and ChatInput here
// import MessageList from './MessageList';
// import ChatInput from './ChatInput';

export default function ChatView() {
  const [messages, setMessages] = useState<Message[]>([]);

  const { mutate: sendMessage, isPending } = useMutation({
    mutationFn: async (text: string) => {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: text }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to send message');
      }
      
      return response.json();
    },
    onSuccess: (data) => {
      // Add AI response
      const aiMessage: Message = {
        id: uuidv4(),
        text: data.response,
        sender: 'ai',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, aiMessage]);
    },
    onError: (error) => {
      console.error('Failed to send message:', error);
      // Optionally show an error message to the user
    }
  });

  const handleSendMessage = (text: string) => {
    // Add user message immediately
    const newUserMessage: Message = {
      id: uuidv4(),
      text,
      sender: 'user',
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, newUserMessage]);

    // Send to backend
    sendMessage(text);
  };

  return (
    // Main container for the chat interface: full width to push scrollbar to edge
    <div className="flex flex-col h-full w-full">
      
      {/* Message display area */}
      <div className="flex-1 overflow-y-auto w-full pb-4">
        <div className="max-w-3xl mx-auto w-full p-4 sm:p-6 space-y-4">
          <p className="text-sm text-muted-foreground text-center">Message list placeholder</p>
          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}
        </div>
      </div>

      {/* Input area */}
      <div className="w-full bg-background">
        <div className="max-w-3xl mx-auto">
          <ChatMessageInput onSendMessage={handleSendMessage} isLoading={isPending} />
        </div>
      </div>
    </div>
  );
} 