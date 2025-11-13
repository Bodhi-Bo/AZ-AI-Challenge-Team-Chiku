"use client";

import { motion, Transition } from "framer-motion";

interface VoiceMascotProps {
  status: "idle" | "listening" | "speaking" | "thinking";
  className?: string;
}

export default function VoiceMascot({
  status,
  className = "",
}: VoiceMascotProps) {
  // ✅ FIX: Proper typing for transitions
  const getTransition = (): Transition => {
    switch (status) {
      case "idle":
        return {
          duration: 4,
          repeat: Infinity,
          ease: "easeInOut" as const, // ✅ Use 'as const'
        };
      case "listening":
        return {
          duration: 1.5,
          repeat: Infinity,
          ease: "easeInOut" as const,
        };
      case "speaking":
        return {
          duration: 0.8,
          repeat: Infinity,
          ease: "easeInOut" as const,
        };
      case "thinking":
        return {
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut" as const,
        };
      default:
        return {};
    }
  };

  const getAnimation = () => {
    switch (status) {
      case "idle":
        return {
          scale: [1, 1.02, 1],
          rotate: [0, 2, 0, -2, 0],
        };
      case "listening":
        return {
          scale: [1, 1.05, 1],
        };
      case "speaking":
        return {
          scale: [1, 1.08, 1.03, 1],
        };
      case "thinking":
        return {
          rotate: [-5, 5, -5],
        };
      default:
        return {};
    }
  };

  return (
    <motion.div
      className={`relative ${className}`}
      animate={getAnimation()}
      transition={getTransition()}
    >
      {/* Glow Effect */}
      <motion.div
        className="absolute inset-0 blur-3xl opacity-50"
        animate={{
          scale: status === "listening" ? [1, 1.2, 1] : [1, 1.1, 1],
          opacity: status === "listening" ? [0.3, 0.6, 0.3] : [0.2, 0.4, 0.2],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut" as const, // ✅ Add 'as const'
        }}
        style={{
          background:
            status === "speaking"
              ? "radial-gradient(circle, #764ba2 0%, #667eea 100%)"
              : "radial-gradient(circle, #667eea 0%, #764ba2 100%)",
        }}
      />

      {/* Mascot */}
      <div className="relative text-[12rem] filter drop-shadow-2xl">🦊</div>

      {/* Status Indicator */}
      {status === "listening" && (
        <motion.div
          className="absolute -bottom-4 left-1/2 -translate-x-1/2"
          animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: "easeInOut" as const, // ✅ Add 'as const'
          }}
        >
          <div className="w-3 h-3 rounded-full bg-red-500" />
        </motion.div>
      )}
    </motion.div>
  );
}
