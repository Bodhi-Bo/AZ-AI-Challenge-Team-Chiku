"use client";

import { useUIStore } from "@/lib/stores/uiStore";
import ChatWindow from "@/components/chat/ChatWindow";
import CalendarWidget from "@/components/calendar/CalendarWidget";
import CalendarExpanded from "@/components/calendar/CalendarExpanded";
import MascotDisplay from "@/components/mascot/MascotDisplay";
import { motion, AnimatePresence } from "framer-motion";

export default function HomePage() {
  const { isCalendarExpanded } = useUIStore();

  return (
    <div className="h-screen w-screen overflow-hidden bg-gradient-to-br from-secondary-50 via-primary-50/20 to-accent-50/10">
      <div className="flex h-full">
        {/* Left Space - 15% */}
        <div className="w-[15%] shrink-0" />

        {/* Chat Window - 50% */}
        <div className="w-[50%] shrink-0 h-full">
          <ChatWindow />
        </div>

        {/* Right Area - 35% (Calendar Widget or Mascot + Animations) */}
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
                key="mascot-area"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.4, ease: "easeInOut" }}
                className="absolute inset-0 flex flex-col items-center justify-center p-8"
              >
                {/* Mascot Display */}
                <div className="flex-1 flex items-center justify-center">
                  <MascotDisplay />
                </div>

                {/* Calendar Widget at Bottom */}
                <div className="w-full">
                  <CalendarWidget />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
