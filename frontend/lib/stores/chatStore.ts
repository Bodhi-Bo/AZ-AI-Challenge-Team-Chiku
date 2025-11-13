// import { create } from 'zustand';

// export interface Message {
//   id: string;
//   role: 'user' | 'assistant';
//   content: string;
//   timestamp: Date;
// }

// interface ChatState {
//   messages: Message[];
//   isLoading: boolean;
//   addMessage: (message: Message) => void;
//   setLoading: (loading: boolean) => void;
//   clearMessages: () => void;
// }

// export const useChatStore = create<ChatState>((set) => ({
//   messages: [],
//   isLoading: false,
//   addMessage: (message) => set((state) => ({
//     messages: [...state.messages, message]
//   })),
//   setLoading: (loading) => set({ isLoading: loading }),
//   clearMessages: () => set({ messages: [] }),
// }));

// lib/stores/chatStore.ts
import { create } from 'zustand';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  isConnected: boolean;

  addMessage: (message: Message) => void;
  setLoading: (loading: boolean) => void;
  setConnected: (connected: boolean) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isLoading: false,
  isConnected: false,

  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),

  setLoading: (loading) => set({ isLoading: loading }),
  setConnected: (connected) => set({ isConnected: connected }),
  clearMessages: () => set({ messages: [] }),
}));
