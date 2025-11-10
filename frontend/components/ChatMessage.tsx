"use client";

import { motion } from "framer-motion";
import { format } from "date-fns";
import { Mic } from "lucide-react";
import type { Message } from "@/types";
import { cn } from "@/lib/utils";

interface ChatMessageProps {
  message: Message;
  isLatest?: boolean;
}

export default function ChatMessage({ message, isLatest }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn(
        "flex w-full mb-3",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3 break-words",
          isUser
            ? "bg-indigo-600 text-white"
            : "bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700"
        )}
      >
        {/* Message content */}
        <p className="text-base leading-relaxed whitespace-pre-wrap">
          {message.content}
        </p>

        {/* Timestamp and voice indicator */}
        <div
          className={cn(
            "flex items-center gap-2 mt-2 text-xs",
            isUser ? "text-indigo-100" : "text-gray-500 dark:text-gray-400"
          )}
        >
          {message.isVoice && (
            <Mic className="h-3 w-3" aria-label="Voice message" />
          )}
          <span>{format(new Date(message.timestamp), "h:mm a")}</span>
        </div>
      </div>
    </motion.div>
  );
}

