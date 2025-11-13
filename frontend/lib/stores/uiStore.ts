import { create } from 'zustand';

interface UIState {
  isCalendarExpanded: boolean;
  setCalendarExpanded: (expanded: boolean) => void;
  toggleCalendar: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  isCalendarExpanded: false,
  setCalendarExpanded: (expanded) => set({ isCalendarExpanded: expanded }),
  toggleCalendar: () => set((state) => ({ isCalendarExpanded: !state.isCalendarExpanded })),
}));
