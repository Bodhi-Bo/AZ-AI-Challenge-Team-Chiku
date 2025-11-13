// hooks/useChatHistory.ts
'use client';

import { useEffect, useState } from 'react';
import { useChatStore } from '@/lib/stores/chatStore';
import { fetchChatHistory } from '@/lib/api/chat-api';

// ✅ GOOD - Fixed version
export function useChatHistory() {
  const chatStore = useChatStore();
  const userId = process.env.NEXT_PUBLIC_USER_ID || 'user_123';
  const [hasLoaded, setHasLoaded] = useState(false);  // ✅ Add guard

  useEffect(() => {
    if (hasLoaded) return;  // ✅ Prevent double-loading

    const loadHistory = async () => {
      try {
        const messages = await fetchChatHistory(userId, 50);

        // ✅ Clear existing messages first
        chatStore.clearMessages();

        // ✅ Then add new ones
        messages.forEach(msg => {
          chatStore.addMessage({
            id: msg._id,
            role: msg.role,
            content: msg.content,
            timestamp: new Date(msg.timestamp)
          });
        });

        setHasLoaded(true);  // ✅ Mark as loaded
      } catch (error) {
        console.error('Failed to load chat history:', error);
      }
    };

    loadHistory();
  }, [userId, hasLoaded, chatStore]);  // ✅ Add all dependencies
}
