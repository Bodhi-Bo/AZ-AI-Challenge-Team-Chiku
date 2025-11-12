"use client";

import { Mic, ArrowUp } from "lucide-react";
import { motion } from "framer-motion";

interface ChatSidebarProps {
  onVoiceClick: () => void;
  onSendClick: () => void;
  isVoiceActive?: boolean;
}

export default function ChatSidebar({
  onVoiceClick,
  onSendClick,
  isVoiceActive = false,
}: ChatSidebarProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50"
    >
      {/* Main Container with Shadow */}
      <div className="bg-white/90 backdrop-blur-xl rounded-full px-6 py-4 shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-white/20">
        <div className="flex items-center gap-4">
          {/* Voice Button */}
          <motion.button
            onClick={onVoiceClick}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={`
              relative h-14 px-6 rounded-full flex items-center gap-3
              font-medium text-base transition-all duration-300
              ${
                isVoiceActive
                  ? "bg-gradient-to-r from-primary-500 to-primary-600 text-white shadow-lg shadow-primary-500/30"
                  : "bg-white text-gray-700 hover:bg-gray-50 border border-gray-200"
              }
            `}
          >
            <motion.div
              animate={isVoiceActive ? { scale: [1, 1.2, 1] } : {}}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              <Mic className="h-5 w-5" />
            </motion.div>
            <span>Voice</span>

            {/* Active Pulse */}
            {isVoiceActive && (
              <motion.div
                className="absolute inset-0 rounded-full border-2 border-primary-400"
                animate={{
                  scale: [1, 1.2, 1.4],
                  opacity: [0.6, 0.3, 0],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeOut",
                }}
              />
            )}
          </motion.button>

          {/* Send Button */}
          <motion.button
            onClick={onSendClick}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="
              h-14 w-14 rounded-full
              bg-gradient-to-r from-gray-700 to-gray-800
              flex items-center justify-center
              shadow-lg shadow-gray-500/20
              hover:shadow-xl
              transition-shadow duration-300
            "
          >
            <ArrowUp color="black" className="h-6 w-6" />
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
}
