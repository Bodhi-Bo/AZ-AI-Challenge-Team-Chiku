"use client";
import { motion } from "framer-motion";

/**
 * This is a light, cloud-themed background for immersive voice mode.
 */
export default function VoiceBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden">
      {/* Light blue gradient base */}
      <motion.div
        className="absolute inset-0"
        animate={{
          background: [
            "linear-gradient(140deg, #e3f0ff 0%, #b3caff 70%, #e5efff 100%)",
            "linear-gradient(120deg, #e5efff 0%, #c3eaff 60%, #b3caff 100%)",
          ],
        }}
        transition={{
          duration: 10,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        style={{ zIndex: 1 }}
      />
      {/* Animated floating clouds */}
      {[...Array(4)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute rounded-2xl opacity-30 blur-xl"
          style={{
            width: `${150 + i * 80}px`,
            height: `${55 + i * 40}px`,
            bottom: `${20 + i * 25}%`,
            left: `${6 + i * 24}%`,
            background: "white",
          }}
          animate={{
            x: [0, 24, -18, 0],
            y: [0, -14, 0],
          }}
          transition={{
            duration: 14 + i * 4,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
}
