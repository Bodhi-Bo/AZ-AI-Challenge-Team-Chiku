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
        className={`w-20 h-20 rounded-full flex items-center justify-center transition-all ${
          isListening
            ? "bg-red-500 hover:bg-red-600"
            : "bg-white/20 hover:bg-white/30"
        }`}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
      >
        {isListening ? (
          <Mic className="w-8 h-8 text-white" />
        ) : (
          <MicOff className="w-8 h-8 text-white" />
        )}
      </motion.button>

      {/* End Call */}
      <motion.button
        onClick={onEnd}
        className="w-16 h-16 rounded-full bg-red-600 hover:bg-red-700 flex items-center justify-center transition-all"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
      >
        <PhoneOff className="w-6 h-6 text-white" />
      </motion.button>
    </div>
  );
}
