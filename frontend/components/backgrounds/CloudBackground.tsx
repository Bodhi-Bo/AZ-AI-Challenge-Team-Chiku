"use client";

import { motion } from "framer-motion";

export default function CloudBackground() {
  const clouds = [
    {
      id: 1,
      x: "20%",
      y: "15%",
      width: 300,
      height: 150,
      duration: 50,
      delay: 0,
    },
    {
      id: 2,
      x: "65%",
      y: "70%",
      width: 280,
      height: 140,
      duration: 60,
      delay: 10,
    },
  ];

  return (
    <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
      {clouds.map((cloud) => (
        <motion.svg
          key={cloud.id}
          className="absolute"
          style={{
            left: cloud.x,
            top: cloud.y,
            width: `${cloud.width}px`,
            height: `${cloud.height}px`,
            opacity: 0.03,
          }}
          viewBox="0 0 200 100"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          animate={{
            y: [0, -20, 0],
            x: [0, 10, 0],
          }}
          transition={{
            duration: cloud.duration,
            repeat: Infinity,
            ease: "easeInOut",
            delay: cloud.delay,
          }}
        >
          {/* Cloud shape using ellipses */}
          <ellipse cx="60" cy="60" rx="35" ry="25" fill="#E0F2FE" />
          <ellipse cx="90" cy="60" rx="35" ry="25" fill="#E0F2FE" />
          <ellipse cx="75" cy="45" rx="30" ry="20" fill="#E0F2FE" />
        </motion.svg>
      ))}
    </div>
  );
}

