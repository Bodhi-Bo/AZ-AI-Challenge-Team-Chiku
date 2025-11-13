"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

interface VoiceTransitionProps {
  isAnimating: boolean;
  children: ReactNode;
}

export default function VoiceTransition({
  isAnimating,
  children,
}: VoiceTransitionProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      className="fixed inset-0"
    >
      <motion.div
        className="absolute inset-0"
        style={{
          border: "6px solid",
          borderImage: "linear-gradient(90deg, #764ba2, #667eea, #b3caff) 1",
          borderRadius: "2.5rem",
        }}
        animate={{
          opacity: [0.3, 0.7, 0.3],
          scale: [0.98, 1.02, 0.98],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      {/* Gradient Wave Effect */}
      <motion.div
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{
          duration: 0.8,
          ease: [0.4, 0, 0.2, 1],
        }}
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(circle at center, rgba(102, 126, 234, 0.2) 0%, transparent 70%)",
        }}
      />

      {/* Content */}
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{
          duration: 0.6,
          delay: 0.3,
          ease: [0.4, 0, 0.2, 1],
        }}
        className="relative h-full"
      >
        {children}
      </motion.div>
    </motion.div>
  );
}
