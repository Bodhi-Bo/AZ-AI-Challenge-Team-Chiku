"use client";

import { useUIStore } from "@/lib/stores/uiStore";
import ChatWindow from "@/components/chat/ChatWindow";
import CalendarSidebar from "@/components/calendar/CalendarSidebar";
import CalendarExpanded from "@/components/calendar/CalendarExpanded";
import CloudBackground from "@/components/backgrounds/CloudBackground";
import { motion, AnimatePresence } from "framer-motion";

export default function HomePage() {
  const { isCalendarExpanded } = useUIStore();

  return (
    <div className="h-screen w-screen overflow-hidden gradient-main relative">
      {/* Cloud Background - Full Page */}
      <CloudBackground />

      {/* Main Content - No header padding */}
      <div className="flex h-full relative z-10">
        {/* Left Space - 15% */}
        <div className="w-[15%] shrink-0" />

        {/* Chat Window - 50% */}
        <div className="w-[50%] shrink-0 h-full">
          <ChatWindow />
        </div>

        {/* Right Area - 35% (Calendar Sidebar or Expanded Calendar) */}
        <div className="flex-1 relative h-full overflow-hidden">
          <AnimatePresence mode="wait">
            {isCalendarExpanded ? (
              <motion.div
                key="calendar-expanded"
                initial={{ opacity: 0, scale: 0.9, x: 50 }}
                animate={{ opacity: 1, scale: 1, x: 0 }}
                exit={{ opacity: 0, scale: 0.9, x: 50 }}
                transition={{ duration: 0.4, ease: "easeInOut" }}
                className="absolute inset-0"
              >
                <CalendarExpanded />
              </motion.div>
            ) : (
              <motion.div
                key="calendar-sidebar"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.4, ease: "easeInOut" }}
                className="absolute inset-0"
              >
                <CalendarSidebar />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
