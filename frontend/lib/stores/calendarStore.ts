import { create } from 'zustand';

export interface Task {
  id: string;
  title: string;
  startTime: Date;
  endTime: Date;
  category?: 'study' | 'break' | 'class' | 'deadline' | 'other';
  completed?: boolean;
}

interface CalendarState {
  tasks: Task[];
  selectedDate: Date;
  addTask: (task: Task) => void;
  updateTask: (id: string, updates: Partial<Task>) => void;
  deleteTask: (id: string) => void;
  setSelectedDate: (date: Date) => void;
  getTasksForDate: (date: Date) => Task[];
}

export const useCalendarStore = create<CalendarState>((set, get) => ({
  tasks: [],
  selectedDate: new Date(),

  addTask: (task) => set((state) => ({
    tasks: [...state.tasks, task]
  })),

  updateTask: (id, updates) => set((state) => ({
    tasks: state.tasks.map((task) =>
      task.id === id ? { ...task, ...updates } : task
    ),
  })),

  deleteTask: (id) => set((state) => ({
    tasks: state.tasks.filter((task) => task.id !== id),
  })),

  setSelectedDate: (date) => set({ selectedDate: date }),

  getTasksForDate: (date) => {
    const tasks = get().tasks;
    return tasks.filter((task) => {
      const taskDate = new Date(task.startTime);
      return (
        taskDate.getDate() === date.getDate() &&
        taskDate.getMonth() === date.getMonth() &&
        taskDate.getFullYear() === date.getFullYear()
      );
    }).sort((a, b) => a.startTime.getTime() - b.startTime.getTime());
  },
}));
