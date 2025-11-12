import { create } from "zustand"
import { parseISO, format } from "date-fns"

export interface Task {
  id: string
  title: string
  description?: string
  startTime: string // ISO string
  endTime: string // ISO string
  category: "study" | "break" | "class" | "deadline" | "overtime" | "meeting" | "personal" | "other"
}

interface CalendarState {
  selectedDate: Date
  tasks: Task[]
  setSelectedDate: (date: Date) => void
  addTask: (task: Task) => void
  updateTask: (id: string, task: Partial<Task>) => void
  deleteTask: (id: string) => void
  getTasksForDate: (date: Date) => Task[]
}

export const useCalendarStore = create<CalendarState>((set, get) => ({
  selectedDate: new Date(),
  tasks: [], // No default events - user starts with empty calendar

  setSelectedDate: (date) => set({ selectedDate: date }),

  addTask: (task) =>
    set((state) => ({
      tasks: [...state.tasks, task],
    })),

  updateTask: (id, updatedTask) =>
    set((state) => ({
      tasks: state.tasks.map((task) =>
        task.id === id ? { ...task, ...updatedTask } : task
      ),
    })),

  deleteTask: (id) =>
    set((state) => ({
      tasks: state.tasks.filter((task) => task.id !== id),
    })),

  getTasksForDate: (date) => {
    const tasks = get().tasks
    const dateStr = format(date, "yyyy-MM-dd")
    return tasks.filter((task) => {
      const taskDate = format(parseISO(task.startTime), "yyyy-MM-dd")
      return taskDate === dateStr
    })
  },
}))
