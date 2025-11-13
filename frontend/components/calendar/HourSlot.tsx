"use client"

import { PlusCircle } from "lucide-react"
import { format } from "date-fns"
import TaskCard from "./TaskCard"
import type { Task } from "@/lib/stores/calendarStore"

interface HourSlotProps {
  hour: number
  isEven: boolean
  isCurrentHour: boolean
  tasks: Task[]
  onClick: () => void
}

export default function HourSlot({
  hour,
  isEven,
  isCurrentHour,
  tasks,
  onClick,
}: HourSlotProps) {
  const formatTime = (hour: number) => {
    const date = new Date()
    date.setHours(hour, 0, 0, 0)
    return format(date, "h:mm a")
  }

  const hasTasks = tasks.length > 0

  return (
    <div
      className={`
        group
        py-6 px-6
        ${isEven ? "bg-white" : "bg-blue-50/20"}
        ${isCurrentHour ? "bg-blue-100/40 border-l-4 border-blue-500" : ""}
        hover:bg-blue-50/30
        cursor-pointer
        transition-all duration-200
        relative
        min-h-[120px]
      `}
      onClick={onClick}
      id={`hour-${hour}`}
    >
      {/* Time Label */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-600">{formatTime(hour)}</span>
        {/* Show "+" on hover when no tasks */}
        {!hasTasks && (
          <PlusCircle className="h-5 w-5 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
        )}
      </div>

      {/* Task Cards or Empty State */}
      <div className="space-y-2">
        {hasTasks ? (
          tasks.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))
        ) : (
          <span className="text-sm text-gray-400 italic">No tasks</span>
        )}
      </div>
    </div>
  )
}

