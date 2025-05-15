"use client"; // If it manages state or uses hooks like useState for messages later

import React, { useState, useEffect } from 'react'; // Added useState and useEffect
import ChatMessageInput from './ChatMessageInput'; // Import the new component
import { Message } from '@/lib/types'; // Import the Message type
import { v4 as uuidv4 } from 'uuid'; // For generating unique IDs
import ChatMessage from './ChatMessage'; // Import the ChatMessage component

// Later, we'll import MessageList and ChatInput here
// import MessageList from './MessageList';
// import ChatInput from './ChatInput';

export default function ChatView() {
  const [messages, setMessages] = useState<Message[]>([]); // Initial messages state

  // Load initial mock messages (can be removed later or fetched from API)
  useEffect(() => {
    setMessages([
      { id: uuidv4(), text: 'Hello there! This is a user message.', sender: 'user', timestamp: new Date().toISOString() },
      { id: uuidv4(), text: 'Hi! This is an AI response.', sender: 'ai', timestamp: new Date().toISOString() },
      { id: uuidv4(), text: 'How are you today?', sender: 'user', timestamp: new Date().toISOString() },
    ]);
  }, []);

  const handleSendMessage = (text: string) => {
    const newUserMessage: Message = {
      id: uuidv4(),
      text,
      sender: 'user',
      timestamp: new Date().toISOString(),
    };
    setMessages((prevMessages) => [...prevMessages, newUserMessage]);

    // Mock AI response
    setTimeout(() => {
      const aiResponse: Message = {
        id: uuidv4(),
        text: "That's interesting! Tell me more.",
        sender: 'ai',
        timestamp: new Date().toISOString(),
      };
      setMessages((prevMessages) => [...prevMessages, aiResponse]);
    }, 1000); // Simulate a delay for AI response
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
          <ChatMessageInput onSendMessage={handleSendMessage} />
        </div>
      </div>
    </div>
  );
} 