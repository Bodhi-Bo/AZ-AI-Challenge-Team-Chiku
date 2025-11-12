"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Header from "@/components/Header";
import ChatInterface from "@/components/ChatInterface";
import CalendarView from "@/components/CalendarView";
import { Calendar, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Home() {
  const [mobileView, setMobileView] = useState<"chat" | "calendar">("chat");
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  return (
    <div className="flex flex-col h-screen bg-white dark:bg-gray-900">
      {/* Header */}
      <Header />

      {/* Main content - Two independent scrollable panels */}
      <main className="flex-1 flex pt-16 min-h-0">
        {/* Chat Side (Left) - Independent scrolling */}
        <AnimatePresence mode="sync">
          {(!isMobile || mobileView === "chat") && (
            <motion.div
              key="chat"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
              className="w-full md:w-2/5 h-full border-r border-gray-100 dark:border-gray-800"
            >
              <ChatInterface />
            </motion.div>
          )}

          {/* Calendar Side (Right) - Independent scrolling */}
          {(!isMobile || mobileView === "calendar") && (
            <motion.div
              key="calendar"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
              className={`${
                isMobile ? "w-full" : "hidden md:flex md:w-3/5"
              } h-full`}
            >
              <CalendarView />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Mobile view toggle */}
      {isMobile && (
        <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50 flex gap-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-full p-2 shadow-2xl">
          <Button
            variant={mobileView === "chat" ? "default" : "ghost"}
            size="sm"
            onClick={() => setMobileView("chat")}
            className="rounded-full px-4"
          >
            <MessageSquare className="h-4 w-4 mr-2" />
            Chat
          </Button>
          <Button
            variant={mobileView === "calendar" ? "default" : "ghost"}
            size="sm"
            onClick={() => setMobileView("calendar")}
            className="rounded-full px-4"
          >
            <Calendar className="h-4 w-4 mr-2" />
            Calendar
          </Button>
        </div>
      )}
    </div>
  );
}
