"use client";

import CalendarWidget from "./CalendarWidget";

export default function CalendarSidebar() {
  return (
    <div className="h-full w-full flex flex-col p-8 bg-transparent">
      {/* Calendar at top */}
      <div className="w-full">
        <CalendarWidget />
      </div>
    </div>
  );
}

