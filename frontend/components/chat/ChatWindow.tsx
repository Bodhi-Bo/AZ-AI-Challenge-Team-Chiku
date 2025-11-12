"use client";

import { useState, useRef, useEffect } from "react";
import { useChatStore } from "@/lib/stores/chatStore";
import { useUIStore } from "@/lib/stores/uiStore";
import { useCalendarStore } from "@/lib/stores/calendarStore";
import { sendMessage } from "@/lib/api/openai";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";

export default function ChatWindow() {
  const { messages, addMessage, setLoading, isLoading } = useChatStore();
  const { setCalendarExpanded } = useUIStore();
  const { addTask } = useCalendarStore();
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: "user" as const,
      content: input.trim(),
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setInput("");
    setLoading(true);

    try {
      // Send to backend webhook
      const response = await sendMessage(input.trim());

      // Handle calendar opening
      if (response.openCalendar) {
        setCalendarExpanded(true);
      }

      // Handle tasks from backend
      if (response.tasks && Array.isArray(response.tasks)) {
        response.tasks.forEach((task) => {
          addTask({
            id: task.id,
            title: task.title,
            startTime: new Date(task.startTime),
            endTime: new Date(task.endTime),
            category: (task.category || "other") as
              | "study"
              | "break"
              | "class"
              | "deadline"
              | "other",
          });
        });
      }

      // Add assistant response
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant" as const,
        content: response.message || "I'm here to help!",
        timestamp: new Date(),
      };

      addMessage(assistantMessage);
    } catch (error) {
      console.error("Failed to send message:", error);

      // Add error message
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant" as const,
        content: "Sorry, I couldn't process that. Please try again.",
        timestamp: new Date(),
      };
      addMessage(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col relative">
      {/* Messages Area - Seamless like ChatGPT */}
      <div className="flex-1 overflow-y-auto px-8 py-12">
        <div className="max-w-3xl mx-auto">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center space-y-4">
                <h1 className="text-4xl font-bold gradient-text">
                  Hi, I&apos;m Chiku! 👋
                </h1>
                <p className="text-secondary-600 text-lg">
                  Your ADHD-friendly study companion
                </p>
                <p className="text-secondary-500">
                  Ask me anything or let&apos;s plan your day together!
                </p>
              </div>
            </div>
          ) : (
            <>
              <MessageList messages={messages} isLoading={isLoading} />
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </div>

      {/* Input Area - Fixed at bottom, seamless */}
      <div className="shrink-0 px-8 py-6 border-t border-secondary-200/50 backdrop-blur-sm bg-white/50">
        <div className="max-w-3xl mx-auto">
          <MessageInput
            value={input}
            onChange={setInput}
            onSend={handleSend}
            disabled={isLoading}
          />
        </div>
      </div>
    </div>
  );
}
