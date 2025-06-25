import { useState, useEffect, useRef, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Message, FileAttachment } from '@/lib/types';
import { useAuth } from '@/features/auth/AuthContext';
import { useTimeline } from "./useTimeline";
import { dedupMessages } from "./dedupMessages";

type UseChatProps = {
  conversationId?: string | null;
};

type UseChatReturn = {
  messages: Message[];
  isConnected: boolean;
  sendMessage: (text: string, files?: FileAttachment[]) => void;
  loading: boolean;
  isReconnecting: boolean;
  // paging
  fetchNextPage: () => void;
  hasNextPage: boolean | undefined;
  isFetchingNextPage: boolean;
};

export function useChat({ conversationId: propConversationId }: UseChatProps = {}): UseChatReturn {
  const { session } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(propConversationId || null);
  const wsRef = useRef<WebSocket | null>(null);
  const currentMessageIdRef = useRef<string | null>(null);
  
  // Heartbeat and reconnection state
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isActiveTabRef = useRef<boolean>(true);
  const shouldReconnectRef = useRef<boolean>(true);
  const isConnectingRef = useRef<boolean>(false); // Prevent multiple simultaneous connections
  const [reconnectAttempts, setReconnectAttempts] = useState<number>(0);
  const [isReconnecting, setIsReconnecting] = useState<boolean>(false);
  // Flag to mark when we purposely close an existing socket so onclose doesn't trigger a reconnection loop
  const intentionalCloseRef = useRef<boolean>(false);

  const { data: msgPages, fetchNextPage, hasNextPage, isFetchingNextPage } = useTimeline(session?.user?.id);

  // Seed messages from history pages (only once or when conversationId changes)
  useEffect(() => {
    if (msgPages) {
      const flat = msgPages.pages.flatMap((p) => p.rows);
      setMessages((prev) => {
        if (prev.length === 0) return flat;
        return dedupMessages([...prev, ...flat]);
      });
    }
  }, [msgPages]);

  // Fetch today's conversation if no conversation ID is provided
  useEffect(() => {
    // If a conversation ID was provided as a prop, use that instead of fetching
    if (propConversationId) {
      setConversationId(propConversationId);
      return;
    }

    // Start fetching immediately when session is available (optimistic loading)
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
        
        // Smart caching with timezone awareness
        const userToday = new Date().toLocaleDateString();
        const cacheKey = `conversation_${session.user?.id}_${userToday}`;
        
        // Check cache first
        const cached = localStorage.getItem(cacheKey);
        if (cached) {
          try {
            const { conversationId: cachedId, date } = JSON.parse(cached);
            if (date === userToday && cachedId) {
              console.log('Today conversation loaded from cache:', cachedId);
              setConversationId(cachedId);
              setLoading(false);
              return;
            }
          } catch {
            // Cache corrupted, fall through to fetch
            localStorage.removeItem(cacheKey);
          }
        }
        
        // Cache miss or different day - fetch fresh
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
        
        // Store in cache for future same-day visits
        localStorage.setItem(cacheKey, JSON.stringify({
          conversationId: data.id,
          date: userToday
        }));
      } catch (error) {
        console.error('Error fetching today conversation:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchTodayConversation();
  }, [session?.access_token, propConversationId]);

  // Ping function to keep connection alive
  const sendPing = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      // Send heartbeat ping
      wsRef.current.send(JSON.stringify({ type: 'ping' }));
      console.log('Heartbeat ping sent');
    }
  };

  // WebSocket connection function (extracted for reuse)
  const connectWebSocket = useCallback(() => {
    if (!conversationId || !session?.access_token) {
      console.log(`WebSocket not connecting, missing ${!conversationId ? 'conversationId' : 'access_token'}`);
      return;
    }

    // Prevent multiple simultaneous connection attempts
    if (isConnectingRef.current) {
      console.log('WebSocket connection already in progress, skipping...');
      return;
    }

    // Set connecting flag
    isConnectingRef.current = true;

    // Close existing connection if any (intentional)
    if (wsRef.current) {
      intentionalCloseRef.current = true;
      wsRef.current.close();
    }

    console.log(`WebSocket connecting to conversation: ${conversationId}`);
    console.log(`With token present: ${!!session.access_token} (${session.access_token.substring(0, 10)}...)`);
    
    // Connect to the WebSocket endpoint with auth token
    const wsHost = process.env.NEXT_PUBLIC_FASTAPI_BACKEND_WS_URL || process.env.NEXT_PUBLIC_FASTAPI_BACKEND_URL || 'localhost:8000';
    console.log('WebSocket host from env:', wsHost);
    
    // Determine protocol based on the host and current window location
    let wsUrl: string;
    
    // If the host already includes a protocol (ws:// or wss://), use it directly
    if (wsHost.startsWith('ws://') || wsHost.startsWith('wss://')) {
      console.log('Using protocol from environment variable');
      // Remove any trailing slash if present
      const cleanHost = wsHost.endsWith('/') ? wsHost.slice(0, -1) : wsHost;
      wsUrl = `${cleanHost}/ws/chat/${conversationId}?token=${encodeURIComponent(session.access_token)}`;
    } else {
      // Otherwise, determine protocol based on current page
      const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      console.log('WebSocket protocol based on current location:', wsProtocol);
      wsUrl = `${wsProtocol}://${wsHost}/ws/chat/${conversationId}?token=${encodeURIComponent(session.access_token)}`;
    }
    
    console.log(`Complete WebSocket URL (token redacted): ${wsUrl.replace(session.access_token, 'TOKEN_REDACTED')}`);
    
    // Create the WebSocket connection
    console.log('Attempting to create WebSocket connection...');
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connection opened successfully");
      setIsConnected(true);
      setIsReconnecting(false);
      setReconnectAttempts(0);
      isConnectingRef.current = false; // Clear connecting flag on success
      
      // Start heartbeat when connected and tab is active
      if (isActiveTabRef.current) {
        startPingInterval();
      }
    };
    
    ws.onclose = (event) => {
      console.error(`WebSocket connection closed with code: ${event.code}, reason: ${event.reason}`);
      setIsConnected(false);
      currentMessageIdRef.current = null;
      isConnectingRef.current = false; // Clear connecting flag on close
      stopPingInterval();
      
      // If we intentionally closed the socket, skip auto-reconnect once
      if (intentionalCloseRef.current) {
        intentionalCloseRef.current = false;
      } else if (shouldReconnectRef.current && isActiveTabRef.current) {
        attemptReconnection();
      }
    };
    
    ws.onerror = (error) => {
      console.error("WebSocket connection error:", error);
      setIsConnected(false);
      currentMessageIdRef.current = null;
      isConnectingRef.current = false; // Clear connecting flag on error
    };
    
    ws.onmessage = (event) => {
      console.log("WebSocket message received:", event.data.substring(0, 50) + "...");
      
      // Ignore ping responses
      if (event.data === JSON.stringify({ type: 'pong' })) {
        return;
      }
      
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
  }, [conversationId, session?.access_token]);

  // Reconnection logic with exponential backoff
  const attemptReconnection = () => {
    if (!shouldReconnectRef.current || reconnectAttempts >= 10) {
      console.log('Max reconnection attempts reached or reconnection disabled');
      setIsReconnecting(false);
      return;
    }

    setIsReconnecting(true);
    const attempt = reconnectAttempts + 1;
    setReconnectAttempts(attempt);
    
    // Exponential backoff: 1s, 2s, 4s, 8s, 16s, max 30s
    const delay = Math.min(1000 * Math.pow(2, attempt - 1), 30000);
    
    console.log(`Attempting reconnection ${attempt}/10 in ${delay}ms`);
    
    reconnectTimeoutRef.current = setTimeout(() => {
      connectWebSocket();
    }, delay);
  };

  // Start ping interval
  const startPingInterval = () => {
    stopPingInterval(); // Clear any existing interval
    
    // Send ping every 4 minutes (240000ms)
    pingIntervalRef.current = setInterval(() => {
      if (isActiveTabRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
        sendPing();
      }
    }, 4 * 60 * 1000);
    
    console.log('Heartbeat interval started (4 minutes)');
  };

  // Stop ping interval
  const stopPingInterval = () => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
      console.log('Heartbeat interval stopped');
    }
  };

  // Page visibility detection for tab switching
  useEffect(() => {
    const handleVisibilityChange = () => {
      const isActive = !document.hidden;
      isActiveTabRef.current = isActive;
      
      console.log(`Tab ${isActive ? 'active' : 'inactive'}`);
      
      if (isActive) {
        // Tab became active
        if (!isConnected && !isConnectingRef.current && conversationId && session?.access_token) {
          // If disconnected and not already connecting, reconnect with small delay
          console.log('Tab active and disconnected - attempting reconnection');
          setReconnectAttempts(0); // Reset attempts for fresh start
          setTimeout(() => {
            // Double-check we're still disconnected and tab is still active
            if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
              connectWebSocket();
            }
          }, 500); // Small delay to prevent rapid-fire attempts
        } else if (isConnected) {
          // If connected, start heartbeat
          startPingInterval();
        }
      } else {
        // Tab became inactive - stop heartbeat to let server timeout naturally
        stopPingInterval();
      }
    };
    
    // Set initial state
    isActiveTabRef.current = !document.hidden;
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [conversationId, session?.access_token, isConnected]);

  // Main WebSocket connection effect
  useEffect(() => {
    // Debug logging for session state
    console.log('useChat debug:', {
      hasSession: !!session,
      hasAccessToken: !!session?.access_token,
      conversationId,
      sessionState: session
    });

    // Only connect if we have both a conversation ID and a token
    if (!conversationId || !session?.access_token) {
      console.log(`WebSocket not connecting, missing ${!conversationId ? 'conversationId' : 'access_token'}`);
      return;
    }

    // Enable reconnection
    shouldReconnectRef.current = true;
    
    // Connect to WebSocket
    connectWebSocket();

    // Cleanup: close the WebSocket connection when the component unmounts
    return () => {
      console.log("Closing WebSocket connection due to component cleanup");
      shouldReconnectRef.current = false; // Disable reconnection
      stopPingInterval();
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [conversationId, session?.access_token, connectWebSocket]);

  const sendMessage = async (text: string, files?: FileAttachment[]) => {
    // Reset the current message ID so a new AI message will be created
    currentMessageIdRef.current = null;
    
    // Add user message immediately with files for optimistic display
    const newUserMessage: Message = {
      id: uuidv4(),
      text,
      sender: 'user',
      timestamp: new Date().toISOString(),
      files: files || []
    };
    setMessages((prev) => [...prev, newUserMessage]);

    // Upload files in background if any
    let fileUrls: string[] = [];
    if (files && files.length > 0 && session?.user?.id) {
      try {
        const { uploadToSupabase } = await import('@/lib/supabase/storage');
        const uploadPromises = files.map(file => 
          file.file ? uploadToSupabase(file.file, session.user.id) : Promise.resolve('')
        );
        fileUrls = await Promise.all(uploadPromises);
        console.log('Files uploaded successfully:', fileUrls);
        
        // Update the message with uploaded URLs and remove uploading state
        setMessages((prev) => 
          prev.map(msg => 
            msg.id === newUserMessage.id 
              ? {
                  ...msg,
                  files: files.map((file, index) => ({
                    ...file,
                    url: fileUrls[index],
                    uploading: false,
                    file: undefined // Remove File object after upload
                  }))
                }
              : msg
          )
        );
      } catch (error) {
        console.error('File upload error:', error);
        // Update message to show upload failed
        setMessages((prev) => 
          prev.map(msg => 
            msg.id === newUserMessage.id 
              ? {
                  ...msg,
                  files: files.map(file => ({
                    ...file,
                    uploading: false,
                    url: undefined // Mark as failed
                  }))
                }
              : msg
          )
        );
      }
    }

    // Send to backend via WebSocket
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      // Send as JSON if we have file URLs, otherwise send as plain text
      if (fileUrls && fileUrls.length > 0) {
        const messageData = {
          text,
          file_urls: fileUrls
        };
        console.log("Sending message with files via WebSocket:", messageData);
        wsRef.current.send(JSON.stringify(messageData));
      } else {
        console.log("Sending message via WebSocket:", text.substring(0, 50) + "...");
        wsRef.current.send(text);
      }
    } else {
      console.error("Cannot send message - WebSocket not connected. State:", wsRef.current?.readyState);
    }
  };

  return {
    messages,
    isConnected,
    sendMessage,
    loading,
    isReconnecting,
    // paging
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage
  };
} 