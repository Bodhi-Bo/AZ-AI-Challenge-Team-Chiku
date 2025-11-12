"use client";

import { motion } from "framer-motion";
import { Message } from "@/lib/stores/chatStore";
import { Loader2 } from "lucide-react";

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
}

export default function MessageList({ messages, isLoading }: MessageListProps) {
  return (
    <div className="space-y-6">
      {messages.map((message, index) => (
        <motion.div
          key={message.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: index * 0.05 }}
          className={`flex ${
            message.role === "user" ? "justify-end" : "justify-start"
          }`}
        >
          <div
            className={`max-w-[80%] rounded-2xl px-5 py-3 ${
              message.role === "user"
                ? "gradient-bg-primary text-white"
                : "bg-white border border-secondary-200 text-secondary-900"
            }`}
          >
            <p className="text-base leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
            <p
              className={`text-xs mt-2 ${
                message.role === "user" ? "text-white/70" : "text-secondary-500"
              }`}
            >
              {new Date(message.timestamp).toLocaleTimeString([], {
                hour: "numeric",
                minute: "2-digit",
              })}
            </p>
          </div>
        </motion.div>
      ))}

      {/* Loading indicator */}
      {isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex justify-start"
        >
          <div className="bg-white border border-secondary-200 rounded-2xl px-5 py-3 flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin text-primary-500" />
            <span className="text-secondary-600">Thinking...</span>
          </div>
        </motion.div>
      )}
    </div>
  );
}
