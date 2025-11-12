"use client";

import { Send, Mic } from "lucide-react";
import { KeyboardEvent } from "react";

interface MessageInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled?: boolean;
}

export default function MessageInput({
  value,
  onChange,
  onSend,
  disabled,
}: MessageInputProps) {
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="relative flex items-end gap-3">
      {/* Voice Button (for future implementation) */}
      <button
        type="button"
        disabled={disabled}
        className="shrink-0 h-12 w-12 rounded-full gradient-bg-accent text-white flex items-center justify-center hover:opacity-90 transition-opacity disabled:opacity-50"
      >
        <Mic className="h-5 w-5" />
      </button>

      {/* Text Input */}
      <div className="flex-1 relative">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Message Chiku..."
          rows={1}
          className="w-full resize-none rounded-2xl border border-secondary-200 bg-white px-5 py-3 pr-12 text-base text-secondary-900 placeholder:text-secondary-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          style={{
            minHeight: "48px",
            maxHeight: "120px",
          }}
        />

        {/* Send Button */}
        <button
          type="button"
          onClick={onSend}
          disabled={disabled || !value.trim()}
          className="absolute right-3 bottom-3 h-6 w-6 flex items-center justify-center text-primary-500 hover:text-primary-600 disabled:text-secondary-300 disabled:cursor-not-allowed transition-colors"
        >
          <Send className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}
