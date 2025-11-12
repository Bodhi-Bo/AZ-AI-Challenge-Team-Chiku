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
          <motion.div
            whileHover={{ scale: 1.01 }}
            transition={{ duration: 0.2 }}
            className={`max-w-[80%] rounded-2xl px-6 py-4 shadow-md ${
              message.role === "user"
                ? "gradient-blue-dark text-white"
                : "gradient-blue-white text-gray-900"
            }`}
          >
            <p className="text-base leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
            <p
              className={`text-xs mt-2 ${
                message.role === "user" ? "text-white/70" : "text-gray-500"
              }`}
            >
              {new Date(message.timestamp).toLocaleTimeString([], {
                hour: "numeric",
                minute: "2-digit",
              })}
            </p>
          </motion.div>
        </motion.div>
      ))}

      {/* Loading indicator */}
      {isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex justify-start"
        >
          <div className="gradient-blue-white rounded-2xl px-6 py-4 flex items-center gap-2 shadow-md">
            <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
            <span className="text-gray-600">Thinking...</span>
          </div>
        </motion.div>
      )}
    </div>
  );
}
