import { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Message } from '@/lib/types';
import { useAuth } from '@/features/auth/AuthContext';

type UseChatProps = {
  conversationId?: string | null;
};

type UseChatReturn = {
  messages: Message[];
  isConnected: boolean;
  sendMessage: (text: string) => void;
};

export function useChat({ conversationId = "test" }: UseChatProps = {}): UseChatReturn {
  const { session } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const currentMessageIdRef = useRef<string | null>(null);

  useEffect(() => {
    // Only connect if we have a token (conversationId now has a default)
    if (!session?.access_token) {
      console.log(`WebSocket not connecting, missing access_token`);
      return;
    }

    console.log(`WebSocket connecting to conversation: ${conversationId}`);
    console.log(`With token present: ${!!session.access_token} (${session.access_token.substring(0, 10)}...)`);
    
    // Connect to the WebSocket endpoint with auth token
    const wsUrl = conversationId === "test" 
      ? `ws://localhost:8000/ws/chat?token=${session.access_token}`
      : `ws://localhost:8000/ws/chat/${conversationId}?token=${session.access_token}`;
    console.log(`WebSocket URL (without token): ${wsUrl.split('?')[0]}`);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connection opened successfully");
      setIsConnected(true);
    };
    
    ws.onclose = (event) => {
      console.error(`WebSocket connection closed with code: ${event.code}, reason: ${event.reason}`);
      setIsConnected(false);
      currentMessageIdRef.current = null;
    };
    
    ws.onerror = (error) => {
      console.error("WebSocket connection error:", error);
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
  }, [conversationId, session?.access_token]);

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