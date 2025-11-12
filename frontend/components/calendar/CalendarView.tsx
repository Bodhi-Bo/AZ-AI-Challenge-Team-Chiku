"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { addDays, subDays } from "date-fns"
import { useCalendarStore } from "@/lib/stores/calendarStore"
import CalendarHeader from "./CalendarHeader"
import DayView from "./DayView"
import CreateTaskDialog from "./CreateTaskDialog"
import type { Task } from "@/lib/stores/calendarStore"

interface CalendarViewProps {
  onClose?: () => void
}

export default function CalendarView({ onClose }: CalendarViewProps) {
  const { selectedDate, setSelectedDate, getTasksForDate, addTask } =
    useCalendarStore()
  const [currentDate, setCurrentDate] = useState(selectedDate)
  const [currentTime, setCurrentTime] = useState(new Date())
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [direction, setDirection] = useState<"next" | "prev">("next")
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedTime, setSelectedTime] = useState<{
    date: Date
    hour: number
  } | null>(null)

  // Update current time every minute
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date())
    }, 60000)
    return () => clearInterval(interval)
  }, [])

  // Sync with store
  useEffect(() => {
    setCurrentDate(selectedDate)
  }, [selectedDate])

  const goToPreviousDay = () => {
    setDirection("prev")
    setIsTransitioning(true)
    const newDate = subDays(currentDate, 1)
    setCurrentDate(newDate)
    setSelectedDate(newDate)
    setTimeout(() => setIsTransitioning(false), 400)
  }

  const goToNextDay = () => {
    setDirection("next")
    setIsTransitioning(true)
    const newDate = addDays(currentDate, 1)
    setCurrentDate(newDate)
    setSelectedDate(newDate)
    setTimeout(() => setIsTransitioning(false), 400)
  }

  const handleDayChange = (event: any, info: any) => {
    const threshold = 100 // pixels

    if (info.offset.x > threshold) {
      // Swipe right - go to previous day
      goToPreviousDay()
    } else if (info.offset.x < -threshold) {
      // Swipe left - go to next day
      goToNextDay()
    }
  }

  const handleHourClick = (hour: number) => {
    setSelectedTime({
      date: currentDate,
      hour,
    })
    setShowCreateModal(true)
  }

  const handleCreateTask = (taskData: Omit<Task, "id">) => {
    const newTask: Task = {
      ...taskData,
      id: Date.now().toString(),
    }
    addTask(newTask)
  }

  const previousDay = subDays(currentDate, 1)
  const nextDay = addDays(currentDate, 1)
  const currentDayTasks = getTasksForDate(currentDate)
  const previousDayTasks = getTasksForDate(previousDay)
  const nextDayTasks = getTasksForDate(nextDay)

  return (
    <div className="h-full w-full bg-transparent relative flex flex-col">
      {/* Header */}
      <CalendarHeader
        currentDate={currentDate}
        onPreviousDay={goToPreviousDay}
        onNextDay={goToNextDay}
        onClose={onClose}
      />

      {/* Horizontal Day View with Blur Edges */}
      <div className="flex-1 relative overflow-hidden">
        {/* Gradient fade on left edge */}
        <div className="absolute left-0 top-0 bottom-0 w-[5%] bg-gradient-to-r from-white to-transparent z-10 pointer-events-none" />

        {/* Previous Day - Blurred */}
        <motion.div
          className="absolute left-0 w-[5%] h-full blur-md opacity-30 pointer-events-none"
          initial={{ opacity: 0.3 }}
          animate={{ opacity: 0.3 }}
        >
          <DayView
            date={previousDay}
            tasks={previousDayTasks}
            currentTime={currentTime}
            onHourClick={() => {}} // Disabled for blurred days
            isActive={false}
          />
        </motion.div>

        {/* Current Day - Main View */}
        <div className="w-[90%] mx-auto h-full">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentDate.toISOString()}
              className="h-full"
              drag="x"
              dragConstraints={{ left: 0, right: 0 }}
              dragElastic={0.2}
              onDragEnd={handleDayChange}
              initial={{
                opacity: 0,
                x: direction === "next" ? 100 : -100,
              }}
              animate={{ opacity: 1, x: 0 }}
              exit={{
                opacity: 0,
                x: direction === "next" ? -100 : 100,
              }}
              transition={{ duration: 0.4, ease: "easeInOut" }}
            >
              <DayView
                date={currentDate}
                tasks={currentDayTasks}
                currentTime={currentTime}
                onHourClick={handleHourClick}
                isActive={true}
              />
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Next Day - Blurred */}
        <motion.div
          className="absolute right-0 w-[5%] h-full blur-md opacity-30 pointer-events-none"
          initial={{ opacity: 0.3 }}
          animate={{ opacity: 0.3 }}
        >
          <DayView
            date={nextDay}
            tasks={nextDayTasks}
            currentTime={currentTime}
            onHourClick={() => {}} // Disabled for blurred days
            isActive={false}
          />
        </motion.div>

        {/* Gradient fade on right edge */}
        <div className="absolute right-0 top-0 bottom-0 w-[5%] bg-gradient-to-l from-white to-transparent z-10 pointer-events-none" />

        {/* Gradient sweep during transition */}
        {isTransitioning && (
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-transparent via-blue-500/10 to-transparent z-20 pointer-events-none"
            initial={{ x: "-100%" }}
            animate={{ x: "100%" }}
            transition={{ duration: 0.6, ease: "linear" }}
            onAnimationComplete={() => setIsTransitioning(false)}
          />
        )}
      </div>

      {/* Create Task Dialog */}
      {selectedTime && (
        <CreateTaskDialog
          open={showCreateModal}
          onOpenChange={setShowCreateModal}
          selectedDate={selectedTime.date}
          selectedHour={selectedTime.hour}
          onCreateTask={handleCreateTask}
        />
      )}
    </div>
  )
}

