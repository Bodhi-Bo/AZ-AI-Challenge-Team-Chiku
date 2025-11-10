/**
 * Type definitions for Chiku application
 */

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isVoice?: boolean;
}

export interface CalendarEvent {
  id: string;
  title: string;
  start: Date;
  end: Date;
  color?: string;
  description?: string;
  category?: 'class' | 'study' | 'break' | 'deadline' | 'other';
}

export interface ChatState {
  messages: Message[];
  isListening: boolean;
  isSpeaking: boolean;
  addMessage: (message: Message) => void;
  setListening: (listening: boolean) => void;
  setSpeaking: (speaking: boolean) => void;
  clearMessages: () => void;
}

export interface CalendarState {
  events: CalendarEvent[];
  addEvent: (event: CalendarEvent) => void;
  updateEvent: (id: string, updates: Partial<CalendarEvent>) => void;
  deleteEvent: (id: string) => void;
}

export interface AppState extends ChatState, CalendarState {}

