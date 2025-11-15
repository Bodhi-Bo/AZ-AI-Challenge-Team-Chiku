"use client";

import { motion } from "framer-motion";
import { Mic, MicOff, PhoneOff } from "lucide-react";

interface VoiceControlsProps {
  isListening: boolean;
  onToggle: () => void;
  onEnd: () => void;
}

export default function VoiceControls({
  isListening,
  onToggle,
  onEnd,
}: VoiceControlsProps) {
  return (
    <div className="flex items-center gap-6">
      {/* Mic Toggle */}
      <motion.button
        onClick={onToggle}
        className={`w-16 h-16 rounded-full flex items-center justify-center transition-all shadow-lg ${
          isListening
            ? "bg-red-500 hover:bg-red-600"
            : "bg-gradient-to-br from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700"
        }`}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
      >
        {isListening ? (
          <Mic className="w-6 h-6 text-black" />
        ) : (
          <MicOff className="w-6 h-6 text-black" />
        )}
      </motion.button>

      {/* End Call */}
      <motion.button
        onClick={onEnd}
        className="w-16 h-16 rounded-full bg-gradient-to-br from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 flex items-center justify-center transition-all shadow-lg"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
      >
        <PhoneOff className="w-6 h-6 text-black" />
      </motion.button>
    </div>
  );
}
