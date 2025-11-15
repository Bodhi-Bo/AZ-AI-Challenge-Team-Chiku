import { create } from 'zustand';

interface UIState {
  isCalendarExpanded: boolean;
  setCalendarExpanded: (expanded: boolean) => void;
  toggleCalendar: () => void;

  calendarTargetDate: Date | null;
  calendarTargetTime: Date | null;
  shouldOpenCalendarFromWidget: boolean;

  setCalendarTargetDate: (date: Date | null) => void;
  setCalendarTargetTime: (time: Date | null) => void;
  setShouldOpenCalendarFromWidget: (shouldOpen: boolean) => void;

  navigateCalendarTo: (date: Date, time?: Date) => void;
}

export const useUIStore = create<UIState>((set) => ({
  isCalendarExpanded: false,
  setCalendarExpanded: (expanded) => set({ isCalendarExpanded: expanded }),
  toggleCalendar: () => set((state) => ({ isCalendarExpanded: !state.isCalendarExpanded })),

  calendarTargetDate: null,
  calendarTargetTime: null,
  shouldOpenCalendarFromWidget: false,

  setCalendarTargetDate: (date) => set({ calendarTargetDate: date }),
  setCalendarTargetTime: (time) => set({ calendarTargetTime: time }),
  setShouldOpenCalendarFromWidget: (shouldOpen) => set({ shouldOpenCalendarFromWidget: shouldOpen }),

  navigateCalendarTo: (date: Date, time?: Date) => set({
    calendarTargetDate: date,
    calendarTargetTime: time || null,
    isCalendarExpanded: true,
    shouldOpenCalendarFromWidget: true,
  }),
}));
