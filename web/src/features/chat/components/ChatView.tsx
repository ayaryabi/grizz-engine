"use client"; // If it manages state or uses hooks like useState for messages later

import React, { useState, useEffect, useRef } from 'react';
import ChatMessageInput from './ChatMessageInput';
import ChatMessageList from './ChatMessageList';
import { Message } from '@/lib/types';
import { v4 as uuidv4 } from 'uuid';

// Later, we'll import MessageList and ChatInput here
// import MessageList from './MessageList';
// import ChatInput from './ChatInput';

export default function ChatView() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect to the echo WebSocket endpoint
    const ws = new WebSocket('ws://localhost:8000/ws/echo');
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
    };
    ws.onclose = () => {
      setIsConnected(false);
    };
    ws.onerror = () => {
      setIsConnected(false);
    };
    ws.onmessage = (event) => {
      // Add AI (echoed) message
      const aiMessage: Message = {
        id: uuidv4(),
        text: event.data,
        sender: 'ai',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, aiMessage]);
    };

    return () => {
      ws.close();
    };
  }, []);

  const handleSendMessage = (text: string) => {
    // Add user message immediately
    const newUserMessage: Message = {
      id: uuidv4(),
      text,
      sender: 'user',
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, newUserMessage]);

    // Send to backend via WebSocket
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(text);
    }
  };

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
          <ChatMessageInput onSendMessage={handleSendMessage} disabled={!isConnected} />
        </div>
      </div>
    </div>
  );
} 