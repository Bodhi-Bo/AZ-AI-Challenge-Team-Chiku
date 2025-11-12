"use client";

import { useState, useRef, useEffect } from "react";
import { useChatStore } from "@/lib/stores/chatStore";
import { useUIStore } from "@/lib/stores/uiStore";
import { useCalendarStore } from "@/lib/stores/calendarStore";
import { motion } from "framer-motion";
import { ScrollArea } from "@/components/ui/scroll-area";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";
import CloudBackground from "@/components/backgrounds/CloudBackground";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useChatHistory } from "@/hooks/useChatHistory";
import { useCalendar } from "@/hooks/useCalendar";

export default function ChatWindow() {
  const { messages, isLoading } = useChatStore();
  const { setCalendarExpanded } = useUIStore();
  const [input, setInput] = useState("");

  // Initialize WebSocket and data loading
  const { sendMessage: sendWebSocketMessage } = useWebSocket();
  useChatHistory(); // Load previous messages
  useCalendar(); // Load calendar events
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    console.log("📤 Sending message:", input.trim());

    // Send via WebSocket (hook handles everything)
    sendWebSocketMessage(input.trim());

    // Clear input
    setInput("");
  };

  const handleVoiceClick = () => {
    setIsVoiceActive(!isVoiceActive);
    // TODO: Implement voice functionality
    console.log("Voice clicked:", !isVoiceActive);
  };

  return (
    <div className="h-full flex flex-col relative bg-transparent">
      {/* Cloud Background */}
      <CloudBackground />

      {/* Messages Area */}
      <div className="flex-1 overflow-hidden relative z-10">
        <ScrollArea className="h-full">
          <div className="px-8 py-12">
            <div className="max-w-4xl mx-auto">
              {messages.length === 0 ? (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6 }}
                  className="flex items-center justify-center min-h-[60vh]"
                >
                  <div className="text-center space-y-6 max-w-2xl">
                    <motion.div
                      animate={{
                        y: [0, -10, 0],
                      }}
                      transition={{
                        duration: 3,
                        repeat: Infinity,
                        ease: "easeInOut",
                      }}
                      className="inline-block p-4 mb-4"
                    >
                      <span className="text-8xl">🦊</span>
                    </motion.div>
                    <h1 className="text-5xl font-bold text-blue-700">
                      Hi, I&apos;m Chiku!
                    </h1>
                    <p className="text-xl text-gray-600">
                      Your ADHD-friendly study companion
                    </p>
                    <p className="text-gray-500 max-w-md mx-auto">
                      I can help you break down tasks, manage your schedule, and
                      stay focused. What would you like to work on today?
                    </p>
                  </div>
                </motion.div>
              ) : (
                <>
                  {/* Mascot at top when chat starts */}
                  <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4 }}
                    className="flex justify-center mb-8"
                  >
                    <div className="text-6xl">🦊</div>
                  </motion.div>
                  <MessageList messages={messages} isLoading={isLoading} />
                  <div ref={messagesEndRef} />
                </>
              )}
            </div>
          </div>
        </ScrollArea>
      </div>

      {/* Input Area - Fixed at bottom */}
      <div className="shrink-0 px-8 pb-8 pt-6 relative z-10">
        <div className="max-w-[700px] mx-auto">
          <MessageInput
            value={input}
            onChange={setInput}
            onSend={handleSend}
            disabled={isLoading}
            inputRef={inputRef}
            onVoiceClick={handleVoiceClick}
            isVoiceActive={isVoiceActive}
          />
        </div>
      </div>
    </div>
  );
}
