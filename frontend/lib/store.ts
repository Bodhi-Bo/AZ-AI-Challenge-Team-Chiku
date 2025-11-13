/**
 * Zustand store for managing application state
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Message, CalendarEvent, AppState } from '@/types';

interface StoreState {
  // Chat state
  messages: Message[];
  isListening: boolean;
  isSpeaking: boolean;
  
  // Calendar state
  events: CalendarEvent[];
  
  // Chat actions
  addMessage: (message: Message) => void;
  setListening: (listening: boolean) => void;
  setSpeaking: (speaking: boolean) => void;
  clearMessages: () => void;
  
  // Calendar actions
  addEvent: (event: CalendarEvent) => void;
  updateEvent: (id: string, updates: Partial<CalendarEvent>) => void;
  deleteEvent: (id: string) => void;
}

export const useStore = create<StoreState>()(
  persist(
    (set) => ({
      // Initial state
      messages: [],
      isListening: false,
      isSpeaking: false,
      events: [],
      
      // Chat actions
      addMessage: (message) =>
        set((state) => ({
          messages: [...state.messages, message],
        })),
      
      setListening: (listening) =>
        set({ isListening: listening }),
      
      setSpeaking: (speaking) =>
        set({ isSpeaking: speaking }),
      
      clearMessages: () =>
        set({ messages: [] }),
      
      // Calendar actions
      addEvent: (event) =>
        set((state) => ({
          events: [...state.events, event],
        })),
      
      updateEvent: (id, updates) =>
        set((state) => ({
          events: state.events.map((event) =>
            event.id === id ? { ...event, ...updates } : event
          ),
        })),
      
      deleteEvent: (id) =>
        set((state) => ({
          events: state.events.filter((event) => event.id !== id),
        })),
    }),
    {
      name: 'chiku-storage',
      partialize: (state) => ({
        messages: state.messages,
        events: state.events,
      }),
    }
  )
);

