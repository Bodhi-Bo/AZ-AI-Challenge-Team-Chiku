"use client";

import { motion } from "framer-motion";
import { useChatStore } from "@/lib/stores/chatStore";

export default function MascotDisplay() {
  const { isLoading } = useChatStore();

  return (
    <div className="relative">
      {/* Glow Effect */}
      <motion.div
        className="absolute inset-0 rounded-full blur-3xl opacity-30"
        animate={{
          background: isLoading
            ? "radial-gradient(circle, rgba(99, 102, 241, 0.4), transparent 70%)"
            : "radial-gradient(circle, rgba(236, 72, 153, 0.3), transparent 70%)",
          scale: [1, 1.2, 1],
        }}
        transition={{
          background: { duration: 0.5 },
          scale: { duration: 3, repeat: Infinity },
        }}
      />

      {/* Mascot Circle */}
      <motion.div
        className="relative w-64 h-64 rounded-full gradient-bg-primary flex items-center justify-center shadow-2xl"
        animate={{
          y: [0, -15, 0],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      >
        <span className="text-8xl">🦊</span>
      </motion.div>

      {/* Status Text */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center mt-6 text-secondary-600 font-medium"
      >
        {isLoading ? "Thinking..." : "Ready to help!"}
      </motion.p>
    </div>
  );
}
