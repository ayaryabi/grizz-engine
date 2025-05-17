import { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Message } from '@/lib/types';

type UseChatReturn = {
  messages: Message[];
  isConnected: boolean;
  sendMessage: (text: string) => void;
};

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const currentMessageIdRef = useRef<string | null>(null);

  useEffect(() => {
    // Connect to the WebSocket endpoint
    const ws = new WebSocket('ws://localhost:8000/ws/echo');
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      currentMessageIdRef.current = null;
    };
    
    ws.onerror = () => {
      setIsConnected(false);
      currentMessageIdRef.current = null;
    };
    
    ws.onmessage = (event) => {
      // Append to current AI message or create a new one
      if (!currentMessageIdRef.current) {
        // Start a new AI message
        const messageId = uuidv4();
        currentMessageIdRef.current = messageId;
        
        const aiMessage: Message = {
          id: messageId,
          text: event.data,
          sender: 'ai',
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, aiMessage]);
      } else {
        // Append to existing message
        setMessages((prev) => {
          const updated = [...prev];
          const lastMessage = updated[updated.length - 1];
          if (lastMessage && lastMessage.id === currentMessageIdRef.current) {
            updated[updated.length - 1] = {
              ...lastMessage,
              text: lastMessage.text + event.data,
            };
          }
          return updated;
        });
      }
    };

    // Cleanup: close the WebSocket connection when the component unmounts
    return () => {
      ws.close();
    };
  }, []);

  const sendMessage = (text: string) => {
    // Reset the current message ID so a new AI message will be created
    currentMessageIdRef.current = null;
    
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

  return {
    messages,
    isConnected,
    sendMessage
  };
} 