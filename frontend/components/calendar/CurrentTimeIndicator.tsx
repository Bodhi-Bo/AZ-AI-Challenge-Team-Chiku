"use client"

import { motion } from "framer-motion"
import { format } from "date-fns"

interface CurrentTimeIndicatorProps {
  currentTime: Date
  isToday: boolean
  hourHeight: number // Height of each hour slot in pixels
}

export default function CurrentTimeIndicator({
  currentTime,
  isToday,
  hourHeight,
}: CurrentTimeIndicatorProps) {
  if (!isToday) return null

  // Calculate position based on current time
  const hours = currentTime.getHours()
  const minutes = currentTime.getMinutes()
  const position = (hours + minutes / 60) * hourHeight

  return (
    <motion.div
      className="absolute left-0 right-0 z-20 flex items-center pointer-events-none"
      style={{ top: `${position}px` }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="h-3 w-3 rounded-full bg-red-500 -ml-1.5 shadow-sm" />
      <div className="flex-1 h-0.5 bg-red-500" />
      <span className="text-xs font-medium text-red-500 ml-2 bg-white/90 px-1.5 py-0.5 rounded shadow-sm">
        {format(currentTime, "h:mm a")}
      </span>
    </motion.div>
  )
}

