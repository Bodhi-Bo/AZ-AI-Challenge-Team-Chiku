"use client";

import { useUIStore } from "@/lib/stores/uiStore";
import CalendarView from "./CalendarView";

export default function CalendarExpanded() {
  const { setCalendarExpanded } = useUIStore();

  return <CalendarView onClose={() => setCalendarExpanded(false)} />;
}
