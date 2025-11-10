"use client";

import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState, useRef } from "react";

type EmotionType =
  | "idle"
  | "happy"
  | "thinking"
  | "celebrating"
  | "tired"
  | "encouraging"
  | "sleeping";

interface ChikuMascotProps {
  emotion?: EmotionType;
  size?: number;
  onClick?: () => void;
  showMessage?: boolean;
  message?: string;
}

const emotionMessages = {
  idle: "Hi! I'm Chiku 👋",
  happy: "Great work! 🎉",
  thinking: "Hmm, let me think... 🤔",
  celebrating: "Amazing! You did it! ✨",
  tired: "Time for a break? 😴",
  encouraging: "You've got this! 💪",
  sleeping: "Rest well! 💤",
};

// Map emotions to available image files
const emotionImageMap: Record<EmotionType, string> = {
  idle: "Neutral peaceful,.jpg",
  happy: "Happy.jpg",
  thinking: "Gentle.jpg",
  celebrating: "Happy and surprised.jpg",
  tired: "Slightly uneasy.jpg",
  encouraging: "Winking.jpg",
  sleeping: "Gentle.jpg",
};

export default function ChikuMascot({
  emotion = "idle",
  size = 150,
  onClick,
  showMessage = false,
  message,
}: ChikuMascotProps) {
  const [displayMessage, setDisplayMessage] = useState(false);
  const previousEmotionRef = useRef(emotion);

  // Show message when emotion changes
  useEffect(() => {
    if (emotion !== previousEmotionRef.current && emotion !== "idle") {
      previousEmotionRef.current = emotion;

      const showTimer = setTimeout(() => setDisplayMessage(true), 0);
      const hideTimer = setTimeout(() => setDisplayMessage(false), 3000);
      return () => {
        clearTimeout(showTimer);
        clearTimeout(hideTimer);
      };
    }
    previousEmotionRef.current = emotion;
  }, [emotion]);

  const finalMessage = message || emotionMessages[emotion];

  return (
    <div className="relative">
      {/* Speech Bubble */}
      <AnimatePresence>
        {(displayMessage || showMessage) && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.8 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.8 }}
            transition={{ type: "spring", duration: 0.4 }}
            className="absolute bottom-full mb-3 left-1/2 -translate-x-1/2 whitespace-nowrap z-10"
          >
            <div className="bg-white rounded-2xl shadow-xl px-4 py-2 border border-gray-100">
              <p className="text-sm font-medium text-gray-800">
                {finalMessage}
              </p>
              {/* Speech bubble tail */}
              <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-2">
                <div className="w-4 h-4 bg-white border-r border-b border-gray-100 rotate-45" />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Mascot Container */}
      <motion.div
        className="relative cursor-pointer select-none"
        style={{ width: size, height: size }}
        onClick={onClick}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        animate={{
          y: [0, -8, 0], // Floating animation
        }}
        transition={{
          y: {
            duration: 3,
            repeat: Infinity,
            ease: "easeInOut",
          },
        }}
      >
        {/* Glow effect that changes color by emotion */}
        <motion.div
          className="absolute inset-0 rounded-full blur-2xl opacity-40 -z-10"
          animate={{
            background: getEmotionGlow(emotion),
            scale: [1, 1.2, 1],
          }}
          transition={{
            background: { duration: 0.5 },
            scale: { duration: 2, repeat: Infinity },
          }}
        />

        {/* Mascot Image with Transition */}
        <AnimatePresence mode="wait">
          <motion.div
            key={emotion}
            initial={{
              opacity: 0,
              scale: 0.5,
              rotate: -20,
            }}
            animate={{
              opacity: 1,
              scale: 1,
              rotate: 0,
            }}
            exit={{
              opacity: 0,
              scale: 0.5,
              rotate: 20,
            }}
            transition={{
              type: "spring",
              stiffness: 300,
              damping: 20,
              duration: 0.5,
            }}
            className="relative w-full h-full"
          >
            <Image
              src={`/mascot/${emotionImageMap[emotion]}`}
              alt={`Chiku ${emotion}`}
              fill
              className="object-contain drop-shadow-2xl rounded-full"
              priority={emotion === "idle"}
            />
          </motion.div>
        </AnimatePresence>

        {/* Celebration Confetti Effect */}
        {emotion === "celebrating" && (
          <div className="absolute inset-0 pointer-events-none">
            {[...Array(8)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute left-1/2 top-1/2"
                initial={{
                  x: 0,
                  y: 0,
                  scale: 0,
                  opacity: 1,
                }}
                animate={{
                  x: Math.cos((i * 45 * Math.PI) / 180) * 60,
                  y: Math.sin((i * 45 * Math.PI) / 180) * 60,
                  scale: [0, 1, 0.8, 0],
                  opacity: [1, 1, 1, 0],
                  rotate: [0, 360],
                }}
                transition={{
                  duration: 1.2,
                  repeat: Infinity,
                  delay: i * 0.1,
                  ease: "easeOut",
                }}
              >
                <span className="text-xl">
                  {["🎉", "✨", "⭐", "💫"][i % 4]}
                </span>
              </motion.div>
            ))}
          </div>
        )}

        {/* Thinking Dots */}
        {emotion === "thinking" && (
          <motion.div
            className="absolute -top-6 right-0"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <div className="bg-white rounded-full px-3 py-2 shadow-lg flex gap-1">
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  className="w-2 h-2 bg-indigo-400 rounded-full"
                  animate={{
                    y: [0, -6, 0],
                    opacity: [0.3, 1, 0.3],
                  }}
                  transition={{
                    duration: 1,
                    repeat: Infinity,
                    delay: i * 0.2,
                  }}
                />
              ))}
            </div>
          </motion.div>
        )}

        {/* Sleeping ZZZ */}
        {emotion === "sleeping" && (
          <div className="absolute -top-4 -right-2">
            {["z", "Z", "Z"].map((letter, i) => (
              <motion.span
                key={i}
                className="absolute text-2xl font-bold text-indigo-300"
                style={{
                  left: i * 12,
                  top: i * -12,
                }}
                animate={{
                  y: [0, -20, -40],
                  opacity: [0, 1, 0],
                  scale: [0.5, 1, 1.5],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  delay: i * 0.4,
                }}
              >
                {letter}
              </motion.span>
            ))}
          </div>
        )}

        {/* Tired Sweat Drop */}
        {emotion === "tired" && (
          <motion.div
            className="absolute right-2 top-4"
            animate={{
              y: [0, 15],
              opacity: [1, 0],
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
            }}
          >
            <span className="text-2xl">💧</span>
          </motion.div>
        )}

        {/* Encouraging Sparkle */}
        {emotion === "encouraging" && (
          <motion.div
            className="absolute -right-4 top-1/4"
            animate={{
              scale: [1, 1.3, 1],
              rotate: [0, 180, 360],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
            }}
          >
            <span className="text-3xl">💪</span>
          </motion.div>
        )}

        {/* Happy Sparkles */}
        {emotion === "happy" && (
          <>
            {[0, 1].map((i) => (
              <motion.div
                key={i}
                className="absolute"
                style={{
                  left: i === 0 ? "10%" : "80%",
                  top: "20%",
                }}
                animate={{
                  scale: [0, 1, 0],
                  rotate: [0, 180],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  delay: i * 0.5,
                }}
              >
                <span className="text-xl">✨</span>
              </motion.div>
            ))}
          </>
        )}
      </motion.div>
    </div>
  );
}

// Helper function for emotion-based glow colors
function getEmotionGlow(emotion: EmotionType): string {
  const glows = {
    idle: "radial-gradient(circle, rgba(167, 139, 250, 0.3), transparent 70%)",
    happy: "radial-gradient(circle, rgba(251, 191, 36, 0.4), transparent 70%)",
    thinking:
      "radial-gradient(circle, rgba(99, 102, 241, 0.3), transparent 70%)",
    celebrating:
      "radial-gradient(circle, rgba(236, 72, 153, 0.5), transparent 70%)",
    tired: "radial-gradient(circle, rgba(107, 114, 128, 0.2), transparent 70%)",
    encouraging:
      "radial-gradient(circle, rgba(34, 197, 94, 0.4), transparent 70%)",
    sleeping:
      "radial-gradient(circle, rgba(139, 92, 246, 0.2), transparent 70%)",
  };
  return glows[emotion];
}
