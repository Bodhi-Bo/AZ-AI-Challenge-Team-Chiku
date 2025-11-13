"use client";

import { motion, AnimatePresence } from "framer-motion";

interface TranscriptionDisplayProps {
  text: string;
  isListening: boolean;
  className?: string;
}

export default function TranscriptionDisplay({
  text,
  isListening,
  className = "",
}: TranscriptionDisplayProps) {
  return (
    <motion.div
      className={`max-w-2xl text-center ${className}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <AnimatePresence mode="wait">
        {text ? (
          <motion.p
            key={text}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="text-2xl font-medium text-white mb-2"
          >
            {text}
          </motion.p>
        ) : (
          <motion.p
            key="placeholder"
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.6 }}
            className="text-xl text-white/60"
          >
            {isListening ? "Listening..." : "Tap to speak"}
          </motion.p>
        )}
      </AnimatePresence>

      {isListening && (
        <motion.div
          className="flex items-center justify-center gap-1 mt-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="w-2 h-2 rounded-full bg-white"
              animate={{
                scale: [1, 1.5, 1],
                opacity: [0.4, 1, 0.4],
              }}
              transition={{
                duration: 1,
                repeat: Infinity,
                delay: i * 0.2,
              }}
            />
          ))}
        </motion.div>
      )}
    </motion.div>
  );
}
