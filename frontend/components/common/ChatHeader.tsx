"use client";

import { motion } from "framer-motion";

export default function ChatHeader() {
  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="
        sticky top-0 z-40
        bg-white/80 backdrop-blur-xl
        border-b border-gray-100
        shadow-[0_2px_20px_rgba(0,0,0,0.08)]
      "
    >
      <div className="max-w-4xl mx-auto px-8 py-6">
        <h1
          className="
          text-3xl font-bold
          bg-gradient-to-r from-primary-600 via-primary-500 to-accent-500
          bg-clip-text text-transparent
          tracking-tight
        "
        >
          Chiku
        </h1>
      </div>
    </motion.header>
  );
}
