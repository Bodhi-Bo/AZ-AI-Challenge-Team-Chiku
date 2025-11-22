"use client";

import { useUIStore } from "@/lib/stores/uiStore";
import CalendarView from "./CalendarView";

export default function CalendarExpanded() {
  const {
    setCalendarExpanded,
    calendarTargetDate,
    calendarTargetTime,
    setCalendarTargetDate,
    setCalendarTargetTime,
  } = useUIStore();

  const handleClose = () => {
    setCalendarExpanded(false);
    // Reset navigation state
    setCalendarTargetDate(null);
    setCalendarTargetTime(null);
  };

  return (
    <CalendarView
      onClose={handleClose}
      targetDate={calendarTargetDate || undefined}
      targetTime={calendarTargetTime || undefined}
    />
  );
}
