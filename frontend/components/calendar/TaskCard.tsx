"use client"

import { motion } from "framer-motion"
import { format } from "date-fns"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { Task } from "@/lib/stores/calendarStore"

interface TaskCardProps {
  task: Task
  isOngoing?: boolean
  progress?: number
}

const categoryConfig = {
  study: {
    emoji: "📚",
    borderColor: "border-blue-500",
    bgColor: "bg-blue-100",
    textColor: "text-blue-700",
  },
  break: {
    emoji: "☕",
    borderColor: "border-green-500",
    bgColor: "bg-green-100",
    textColor: "text-green-700",
  },
  class: {
    emoji: "🎓",
    borderColor: "border-purple-500",
    bgColor: "bg-purple-100",
    textColor: "text-purple-700",
  },
  deadline: {
    emoji: "⏰",
    borderColor: "border-red-500",
    bgColor: "bg-red-100",
    textColor: "text-red-700",
  },
  other: {
    emoji: "📝",
    borderColor: "border-gray-500",
    bgColor: "bg-gray-100",
    textColor: "text-gray-700",
  },
}

export default function TaskCard({ task, isOngoing = false, progress = 0 }: TaskCardProps) {
  const config = categoryConfig[task.category || "other"]

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="group"
    >
      <Card
        className={`
          bg-white/90 backdrop-blur-sm
          border-l-4 ${config.borderColor}
          shadow-sm hover:shadow-md
          transition-all duration-200
          cursor-pointer
          hover:scale-[1.02]
        `}
      >
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">{config.emoji}</span>
                <h3 className="font-semibold text-gray-900">{task.title}</h3>
              </div>
              <p className="text-sm text-gray-600">
                {format(task.startTime, "h:mm a")} - {format(task.endTime, "h:mm a")}
              </p>
            </div>
            <Badge variant="secondary" className={`${config.bgColor} ${config.textColor} border-0`}>
              {task.category || "Other"}
            </Badge>
          </div>

          {/* Progress Bar (if task is ongoing) */}
          {isOngoing && (
            <div className="mt-3">
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <motion.div
                  className={`h-full bg-gradient-to-r ${config.borderColor.replace("border-", "from-")} ${config.borderColor.replace("border-", "to-")}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">{progress}% complete</p>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}

