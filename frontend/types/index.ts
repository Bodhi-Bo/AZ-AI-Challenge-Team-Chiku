// /**
//  * Type definitions for Chiku application
//  */

// export interface Message {
//   id: string;
//   role: 'user' | 'assistant';
//   content: string;
//   timestamp: Date;
//   isVoice?: boolean;
// }

// export interface CalendarEvent {
//   id: string;
//   title: string;
//   start: Date;
//   end: Date;
//   color?: string;
//   description?: string;
//   category?: 'class' | 'study' | 'break' | 'deadline' | 'other';
// }

// export interface ChatState {
//   messages: Message[];
//   isListening: boolean;
//   isSpeaking: boolean;
//   addMessage: (message: Message) => void;
//   setListening: (listening: boolean) => void;
//   setSpeaking: (speaking: boolean) => void;
//   clearMessages: () => void;
// }

// export interface CalendarState {
//   events: CalendarEvent[];
//   addEvent: (event: CalendarEvent) => void;
//   updateEvent: (id: string, updates: Partial<CalendarEvent>) => void;
//   deleteEvent: (id: string) => void;
// }

// export interface AppState extends ChatState, CalendarState {}

// types/index.ts

// ============================================
// MESSAGE TYPES
// ============================================
export interface Message {
  _id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatHistoryResponse {
  user_id: string;
  messages: Message[];
  total: number;
}

// ============================================
// CALENDAR EVENT TYPES
// ============================================
export interface CalendarEvent {
  _id: string;
  user_id: string;
  title: string;
  date: string;                // YYYY-MM-DD
  start_time: string;          // HH:MM
  duration: number;            // minutes
  description?: string;
  event_datetime: string;      // ISO 8601
  created_at: string;
  updated_at: string;
}

export interface CalendarEventsResponse {
  user_id: string;
  start_date: string;
  end_date: string;
  events: CalendarEvent[];
  total: number;
}

// ============================================
// REMINDER TYPES
// ============================================
export interface Reminder {
  _id: string;
  user_id: string;
  title: string;
  reminder_datetime: string;
  priority: 'low' | 'normal' | 'high';
  status: 'pending' | 'completed' | 'snoozed';
  event_id?: string;
  notes?: string;
}

export interface RemindersResponse {
  user_id: string;
  hours_ahead: number;
  reminders: Reminder[];
  total: number;
}

// ============================================
// WEBSOCKET MESSAGE TYPES
// ============================================
export type ClientMessage =
  | { type: 'message'; text: string }
  | { type: 'ping' };

export type ServerMessage =
  | { type: 'response'; text: string }
  | { type: 'pong' };
