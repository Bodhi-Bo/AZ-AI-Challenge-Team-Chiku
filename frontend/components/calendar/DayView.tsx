"use client"

import { useRef, useEffect } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { format } from "date-fns"
import HourSlot from "./HourSlot"
import CurrentTimeIndicator from "./CurrentTimeIndicator"
import type { Task } from "@/lib/stores/calendarStore"

const HOURS = Array.from({ length: 24 }, (_, i) => i) // 0-23 hours
const HOUR_HEIGHT = 120 // Height of each hour slot in pixels

interface DayViewProps {
  date: Date
  tasks: Task[]
  currentTime: Date
  onHourClick: (hour: number) => void
  isActive?: boolean // Whether this is the active (center) day
}

export default function DayView({
  date,
  tasks,
  currentTime,
  onHourClick,
  isActive = true,
}: DayViewProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const isToday =
    format(currentTime, "yyyy-MM-dd") === format(date, "yyyy-MM-dd")

  // Auto-scroll to current hour on mount if this is today
  useEffect(() => {
    if (isToday && isActive && scrollRef.current) {
      const currentHour = currentTime.getHours()
      const hourElement = document.getElementById(`hour-${currentHour}`)
      if (hourElement) {
        hourElement.scrollIntoView({
          behavior: "smooth",
          block: "center",
        })
      }
    }
  }, [isToday, isActive, currentTime])

  const getTasksForHour = (hour: number) => {
    return tasks.filter((task) => {
      const taskHour = task.startTime.getHours()
      return taskHour === hour
    })
  }

  const isCurrentHour = (hour: number) => {
    return isToday && currentTime.getHours() === hour
  }

  return (
    <div className="relative h-full w-full">
      <ScrollArea className="h-full">
        <div className="relative" ref={scrollRef}>
          {HOURS.map((hour, index) => {
            const hourTasks = getTasksForHour(hour)
            return (
              <HourSlot
                key={hour}
                hour={hour}
                isEven={index % 2 === 0}
                isCurrentHour={isCurrentHour(hour)}
                tasks={hourTasks}
                onClick={() => onHourClick(hour)}
              />
            )
          })}

          {/* Current Time Indicator */}
          {isToday && isActive && (
            <CurrentTimeIndicator
              currentTime={currentTime}
              isToday={isToday}
              hourHeight={HOUR_HEIGHT}
            />
          )}
        </div>
      </ScrollArea>
    </div>
  )
}

