"use client";

import { ArrowUp, Mic } from "lucide-react";
import { KeyboardEvent, RefObject } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface MessageInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled?: boolean;
  inputRef?: RefObject<HTMLInputElement | null>;
  onVoiceClick?: () => void;
  isVoiceActive?: boolean;
}

export default function MessageInput({
  value,
  onChange,
  onSend,
  disabled,
  inputRef,
  onVoiceClick,
  isVoiceActive,
}: MessageInputProps) {
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value);
  };

  return (
    <div className="flex items-center gap-3 gradient-blue-white rounded-full px-4 py-2 shadow-md">
      {/* Text Input - takes most space */}
      <Input
        ref={inputRef}
        value={value}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder="Message Chiku..."
        className="flex-1 border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 text-base placeholder:text-gray-400 h-auto py-2"
      />

      {/* Send Button */}
      <Button
        type="button"
        onClick={onSend}
        disabled={disabled || !value.trim()}
        size="icon"
        className="h-9 w-9 rounded-full bg-blue-600 text-black hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-all flex-shrink-0"
      >
        <ArrowUp className="h-4 w-4" />
      </Button>

      {/* Voice Button */}
      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={onVoiceClick}
        disabled={disabled}
        className={`h-9 w-9 rounded-full hover:bg-blue-50 transition-all flex-shrink-0 ${
          isVoiceActive ? "bg-blue-100" : ""
        }`}
      >
        <Mic className="h-4 w-4 text-blue-600" />
      </Button>
    </div>
  );
}
