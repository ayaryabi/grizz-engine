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
  loading: boolean;
};

export function useChat({ conversationId: propConversationId }: UseChatProps = {}): UseChatReturn {
  const { session } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(propConversationId || null);
  const wsRef = useRef<WebSocket | null>(null);
  const currentMessageIdRef = useRef<string | null>(null);

  // Fetch today's conversation if no conversation ID is provided
  useEffect(() => {
    // If a conversation ID was provided as a prop, use that instead of fetching
    if (propConversationId) {
      setConversationId(propConversationId);
      return;
    }

    // Only fetch if we have an authenticated session
    if (!session?.access_token) {
      return;
    }

    async function fetchTodayConversation() {
      setLoading(true);
      try {
        // Safely check again in case session changed during async operation
        if (!session || !session.access_token) {
          throw new Error('No valid session');
        }
        
        const response = await fetch('/api/chat/today', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.access_token}`
          },
          body: JSON.stringify({ 
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone 
          })
        });

        if (!response.ok) {
          throw new Error('Failed to fetch conversation');
        }

        const data = await response.json();
        console.log('Today conversation fetched:', data);
        setConversationId(data.id);
      } catch (error) {
        console.error('Error fetching today conversation:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchTodayConversation();
  }, [session?.access_token, propConversationId]);

  useEffect(() => {
    // Only connect if we have both a conversation ID and a token
    if (!conversationId || !session?.access_token) {
      console.log(`WebSocket not connecting, missing ${!conversationId ? 'conversationId' : 'access_token'}`);
      return;
    }

    console.log(`WebSocket connecting to conversation: ${conversationId}`);
    console.log(`With token present: ${!!session.access_token} (${session.access_token.substring(0, 10)}...)`);
    
    // Connect to the WebSocket endpoint with auth token
    const wsUrl = `ws://localhost:8000/ws/chat/${conversationId}?token=${session.access_token}`;
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
    sendMessage,
    loading
  };
} 