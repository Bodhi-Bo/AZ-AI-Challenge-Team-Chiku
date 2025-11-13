// import { create } from "zustand"
// import { parseISO, format } from "date-fns"

// export interface Task {
//   id: string
//   title: string
//   description?: string
//   startTime: string // ISO string
//   endTime: string // ISO string
//   category: "study" | "break" | "class" | "deadline" | "overtime" | "meeting" | "personal" | "other"
// }

// interface CalendarState {
//   selectedDate: Date
//   tasks: Task[]
//   setSelectedDate: (date: Date) => void
//   addTask: (task: Task) => void
//   updateTask: (id: string, task: Partial<Task>) => void
//   deleteTask: (id: string) => void
//   getTasksForDate: (date: Date) => Task[]
// }

// export const useCalendarStore = create<CalendarState>((set, get) => ({
//   selectedDate: new Date(),
//   tasks: [], // No default events - user starts with empty calendar

//   setSelectedDate: (date) => set({ selectedDate: date }),

//   addTask: (task) =>
//     set((state) => ({
//       tasks: [...state.tasks, task],
//     })),

//   updateTask: (id, updatedTask) =>
//     set((state) => ({
//       tasks: state.tasks.map((task) =>
//         task.id === id ? { ...task, ...updatedTask } : task
//       ),
//     })),

//   deleteTask: (id) =>
//     set((state) => ({
//       tasks: state.tasks.filter((task) => task.id !== id),
//     })),

//   getTasksForDate: (date) => {
//     const tasks = get().tasks
//     const dateStr = format(date, "yyyy-MM-dd")
//     return tasks.filter((task) => {
//       const taskDate = format(parseISO(task.startTime), "yyyy-MM-dd")
//       return taskDate === dateStr
//     })
//   },
// }))

// lib/stores/calendarStore.ts
// lib/stores/calendarStore.ts
import { create } from "zustand";
import { format } from "date-fns";
import { CalendarEvent } from "@/types";

// Keep Task interface for UI compatibility
export interface Task {
  id: string;
  title: string;
  description?: string;
  startTime: string;
  endTime: string;
  category: "study" | "break" | "class" | "deadline" | "overtime" | "meeting" | "personal" | "other";
}

interface CalendarState {
  selectedDate: Date;
  events: CalendarEvent[];
  dateRangeStart: string | null;
  dateRangeEnd: string | null;
  isLoading: boolean;

  setSelectedDate: (date: Date) => void;
  setEvents: (events: CalendarEvent[]) => void;
  addEvent: (event: CalendarEvent) => void;
  updateEvent: (id: string, event: Partial<CalendarEvent>) => void;
  deleteEvent: (id: string) => void;

  // ✅ Add this method
  getTasksForDate: (date: Date) => Task[];

  setDateRange: (start: string, end: string) => void;
  setLoading: (loading: boolean) => void;
}

export const useCalendarStore = create<CalendarState>((set, get) => ({
  selectedDate: new Date(),
  events: [],
  dateRangeStart: null,
  dateRangeEnd: null,
  isLoading: false,

  setSelectedDate: (date) => set({ selectedDate: date }),

  setEvents: (events) => set({ events }),

  addEvent: (event) =>
    set((state) => ({
      events: [...state.events, event],
    })),

  updateEvent: (id, updatedEvent) =>
    set((state) => ({
      events: state.events.map((event) =>
        event._id === id ? { ...event, ...updatedEvent } : event
      ),
    })),

  deleteEvent: (id) =>
    set((state) => ({
      events: state.events.filter((event) => event._id !== id),
    })),

  // ✅ Conversion happens here once
  getTasksForDate: (date: Date): Task[] => {
    const dateStr = format(date, "yyyy-MM-dd");
    return get().events
      .filter(event => event.date === dateStr)
      .map(event => ({
        id: event._id,
        title: event.title,
        description: event.description,
        startTime: event.event_datetime,
        endTime: new Date(
          new Date(event.event_datetime).getTime() + event.duration * 60000
        ).toISOString(),
        category: "other" as const,
      }));
  },

  setDateRange: (start, end) =>
    set({ dateRangeStart: start, dateRangeEnd: end }),

  setLoading: (loading) => set({ isLoading: loading }),
}));
