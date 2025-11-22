'use client';

import { useEffect, useRef } from 'react';
import { useChatStore } from '@/lib/stores/chatStore';
import { useCalendarStore } from '@/lib/stores/calendarStore';
import { WebSocketService } from '@/lib/api/websocket-service';
import { ServerMessage } from '@/types';
import { fetchEventsRange } from '@/lib/api/calendar-api';

export function useWebSocket() {
  const wsRef = useRef<WebSocketService | null>(null);
  const isInitializedRef = useRef(false); // ✅ Use ref instead of state
  const chatStore = useChatStore();
  const calendarStore = useCalendarStore();
  const userId = process.env.NEXT_PUBLIC_USER_ID || 'user_123';

  useEffect(() => {
    // ✅ CRITICAL: Prevent multiple initializations
    if (isInitializedRef.current) {
      console.log('⚠️ WebSocket already initialized, skipping');
      return;
    }

    console.log('🔌 Initializing WebSocket...');
    isInitializedRef.current = true; // ✅ Mark as initialized (no re-render)

    // Function to sync calendar
    const syncCalendar = async () => {
      console.log('📅 Syncing calendar after message received');
      try {
        const events = await fetchEventsRange(
          userId,
          calendarStore.selectedDate
        );
        calendarStore.setEvents(events);
        console.log('✅ Calendar synced successfully');
      } catch (error) {
        console.error('❌ Failed to sync calendar:', error);
      }
    };

    const ws = new WebSocketService(userId);
    wsRef.current = ws;

    ws.connect(
      // onMessage
      (data: ServerMessage) => {
        console.log('📥 Received from server:', data);

        if (data.type === 'response') {
          chatStore.addMessage({
            id: Date.now().toString(),
            role: 'assistant',
            content: data.text,
            timestamp: new Date(),
          });
          chatStore.setLoading(false);

          // Sync calendar after receiving response
          syncCalendar();
        } else if (data.type === 'pong') {
          console.log('🏓 Pong received');
        }
      },
      // onOpen
      () => {
        console.log('✅ WebSocket ready');
        chatStore.setConnected(true);
      },
      // onClose
      () => {
        console.log('🔌 WebSocket closed');
        chatStore.setConnected(false);
      }
    );

    // Cleanup
    return () => {
      console.log('🧹 Cleaning up WebSocket');
      if (wsRef.current) {
        wsRef.current.disconnect();
        wsRef.current = null;
      }
      isInitializedRef.current = false; // ✅ Reset on cleanup
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // ✅ EMPTY DEPS - Only run once!

  const sendMessage = (text: string) => {
    if (!wsRef.current) {
      console.error('❌ WebSocket not initialized');
      return;
    }

    console.log('📤 Sending message:', text);

    // Add user message immediately
    chatStore.addMessage({
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    });

    // Send to backend
    wsRef.current.sendMessage(text);

    // Show loading
    chatStore.setLoading(true);
  };

  return { sendMessage };
}
