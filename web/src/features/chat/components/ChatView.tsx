"use client"; // If it manages state or uses hooks like useState for messages later

import React, { useState, useEffect } from 'react'; // Added useState and useEffect
import ChatMessageList from './ChatMessageList'; // Import the new component
import ChatMessageInput from './ChatMessageInput'; // Import the new component
import { Message } from '@/lib/types'; // Import the Message type
import { v4 as uuidv4 } from 'uuid'; // For generating unique IDs

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
    // Main container for the chat interface: centered, max-width
    <div className="flex flex-col h-full max-w-3xl mx-auto w-full bg-background">
      
      {/* 1. Message Display Area */}
      {/* 'flex-1' makes this area expand to fill available vertical space. */}
      {/* 'overflow-y-auto' makes ONLY this area scrollable for messages. */}
      {/* 'pb-X' (padding-bottom) is crucial to prevent messages from being hidden *behind* the fixed ChatInput. */}
      {/* The value of X should be roughly the height of your ChatInput bar. Let's use pb-4 as a placeholder. */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 pb-4 space-y-4">
        <p className="text-sm text-muted-foreground text-center">Message list placeholder</p>
        {/* Placeholder for MessageList component - mapping over mockMessages for now */}
        {messages.map((msg) => (
          <div 
            key={msg.id} 
            className={`p-3 rounded-lg shadow-md max-w-md lg:max-w-lg xl:max-w-xl
                        ${msg.sender === 'user' 
                          ? 'bg-primary text-primary-foreground ml-auto rounded-br-none' 
                          : 'bg-muted text-muted-foreground mr-auto rounded-bl-none'}
                      `}
          >
            {msg.text}
          </div>
        ))}
      </div>

      {/* Replace placeholder with ChatMessageInput component */}
      <ChatMessageInput onSendMessage={handleSendMessage} />
      {/* <ChatMessageInput onSendMessage={handleSendMessage} /> // How it will be used later */}

    </div>
  );
} 