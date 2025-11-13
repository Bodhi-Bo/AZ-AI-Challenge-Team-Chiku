"use client";

import { motion } from "framer-motion";

export default function SimpleHeader() {
  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="
        fixed top-0 left-0 right-0 h-16
        bg-gradient-to-r from-blue-500 via-blue-400 to-blue-300
        z-50
        shadow-[0_4px_20px_rgba(59,130,246,0.3)]
        backdrop-blur-sm
      "
    >
      <div className="max-w-7xl mx-auto h-full px-6 flex items-center">
        {/* Logo/Name on the left */}
        <motion.h1
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="
            text-2xl font-bold text-white
            tracking-wide
            drop-shadow-md
          "
        >
          Chiku
        </motion.h1>
      </div>
    </motion.header>
  );
}
