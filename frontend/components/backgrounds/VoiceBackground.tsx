"use client";
import { motion } from "framer-motion";

/**
 * Clean white background with subtle blue gradient accents for voice mode.
 */
export default function VoiceBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden bg-white">
      {/* Subtle blue gradient accent in top corner */}
      <motion.div
        className="absolute top-0 right-0 w-1/3 h-1/3 opacity-20"
        animate={{
          background: [
            "radial-gradient(circle at top right, #e3f0ff 0%, transparent 70%)",
            "radial-gradient(circle at top right, #dae7ff 0%, transparent 65%)",
          ],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      {/* Subtle blue gradient accent in bottom corner */}
      <motion.div
        className="absolute bottom-0 left-0 w-1/3 h-1/3 opacity-15"
        animate={{
          background: [
            "radial-gradient(circle at bottom left, #e8f2ff 0%, transparent 70%)",
            "radial-gradient(circle at bottom left, #dce9ff 0%, transparent 65%)",
          ],
        }}
        transition={{
          duration: 10,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
    </div>
  );
}
