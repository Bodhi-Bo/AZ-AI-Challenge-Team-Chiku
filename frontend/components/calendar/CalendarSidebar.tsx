"use client";

import CalendarWidget from "./CalendarWidget";

export default function CalendarSidebar() {
  return (
    <div className="h-full w-full flex flex-col p-8 bg-transparent relative">
      {/* White gradient overlay at top for seamless blending */}
      <div className="absolute top-0 left-0 right-0 h-48 bg-gradient-to-b from-white via-white/80 to-transparent z-0 pointer-events-none" />

      {/* Calendar at top */}
      <div className="w-full relative z-10">
        <CalendarWidget />
      </div>
    </div>
  );
}
