"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { addDays, subDays, format } from "date-fns";
import { ChevronLeft, ChevronRight, X } from "lucide-react";
import { useCalendarStore } from "@/lib/stores/calendarStore";
import DayView from "./DayView";
import CreateTaskDialog from "./CreateTaskDialog";

import type { Task } from "@/lib/stores/calendarStore";
import TaskListModal from "./TaskListModel";
import { CalendarEvent } from "@/types";

interface CalendarViewProps {
  onClose?: () => void;
  targetDate?: Date; // Optional target date to navigate to
  targetTime?: Date; // Optional target time to scroll to
}

export default function CalendarView({
  onClose,
  targetDate,
  targetTime,
}: CalendarViewProps) {
  const { selectedDate, setSelectedDate, getTasksForDate, addEvent } =
    useCalendarStore();

  const [currentDate, setCurrentDate] = useState(targetDate || selectedDate);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [direction, setDirection] = useState<"next" | "prev">("next");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showTaskListModal, setShowTaskListModal] = useState(false);
  const [selectedTime, setSelectedTime] = useState<{
    date: Date;
    hour: number;
  } | null>(null);
  const [selectedHourTasks, setSelectedHourTasks] = useState<Task[]>([]);

  // ✅ Navigate to target date if provided (SINGLE useEffect, not two!)
  useEffect(() => {
    if (targetDate) {
      const today = new Date();
      const daysDiff = Math.floor(
        (targetDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
      );

      if (daysDiff !== 0) {
        setIsTransitioning(true);
        setDirection(daysDiff > 0 ? "next" : "prev");

        setTimeout(() => {
          setCurrentDate(targetDate);
          setSelectedDate(targetDate);
          setIsTransitioning(false);
        }, 500);
      } else {
        setCurrentDate(targetDate);
        setSelectedDate(targetDate);
      }
    }
  }, [targetDate, setSelectedDate]);

  // ✅ Update current time for red line indicator
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  // ✅ Sync currentDate with selectedDate
  useEffect(() => {
    setCurrentDate(selectedDate);
  }, [selectedDate]);

  // ✅ Navigation functions
  const goToPreviousDay = () => {
    setDirection("prev");
    setIsTransitioning(true);
    const newDate = subDays(currentDate, 1);
    setCurrentDate(newDate);
    setSelectedDate(newDate);
    setTimeout(() => setIsTransitioning(false), 400);
  };

  const goToNextDay = () => {
    setDirection("next");
    setIsTransitioning(true);
    const newDate = addDays(currentDate, 1);
    setCurrentDate(newDate);
    setSelectedDate(newDate);
    setTimeout(() => setIsTransitioning(false), 400);
  };

  const goToToday = () => {
    const today = new Date();
    const daysDiff = Math.floor(
      (today.getTime() - currentDate.getTime()) / (1000 * 60 * 60 * 24)
    );

    if (daysDiff === 0) return;

    setDirection(daysDiff > 0 ? "next" : "prev");
    setIsTransitioning(true);

    setTimeout(() => {
      setCurrentDate(today);
      setSelectedDate(today);
      setIsTransitioning(false);
    }, 400);
  };

  // ✅ Swipe gesture handler
  const handleDayChange = (
    _event: MouseEvent | TouchEvent | PointerEvent,
    info: { offset: { x: number; y: number } }
  ) => {
    const threshold = 80;
    if (info.offset.x > threshold) {
      goToPreviousDay();
    } else if (info.offset.x < -threshold) {
      goToNextDay();
    }
  };

  // ✅ Event handlers
  const handleHourClick = (hour: number) => {
    setSelectedTime({ date: currentDate, hour });
    setShowCreateModal(true);
  };

  const handleShowMoreTasks = (tasks: Task[]) => {
    setSelectedHourTasks(tasks);
    setShowTaskListModal(true);
  };

  const handleCreateTask = (taskData: Omit<Task, "id">) => {
    const startTime = new Date(taskData.startTime);
    const endTime = new Date(taskData.endTime);
    const duration = Math.round(
      (endTime.getTime() - startTime.getTime()) / 60000
    );

    const newEvent: CalendarEvent = {
      _id: Date.now().toString(),
      user_id: process.env.NEXT_PUBLIC_USER_ID || "user_123",
      title: taskData.title,
      date: format(startTime, "yyyy-MM-dd"),
      start_time: format(startTime, "HH:mm"),
      duration: duration,
      description: taskData.description,
      event_datetime: startTime.toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    addEvent(newEvent);
  };

  // ✅ Get tasks for days
  const previousDay = subDays(currentDate, 1);
  const nextDay = addDays(currentDate, 1);
  const currentDayTasks = getTasksForDate(currentDate);
  const previousDayTasks = getTasksForDate(previousDay);
  const nextDayTasks = getTasksForDate(nextDay);

  return (
    <div className="h-full w-full bg-gradient-to-br from-blue-50 to-white relative flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 px-6 py-4 flex items-center justify-between bg-white/80 backdrop-blur-sm shadow-sm">
        <div className="flex items-center gap-3">
          <div>
            <h2 className="text-xl font-semibold tracking-tight text-gray-900">
              {format(currentDate, "EEEE, MMMM d")}
            </h2>
            <p className="text-sm text-gray-500">
              {format(currentDate, "yyyy")}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={goToPreviousDay}
            className="inline-flex items-center justify-center rounded-lg text-sm font-medium transition-all hover:bg-blue-50 h-10 w-10 shadow-sm hover:shadow-md"
            disabled={isTransitioning}
          >
            <ChevronLeft className="h-4 w-4" />
          </button>

          <button
            onClick={goToToday}
            className="inline-flex items-center justify-center rounded-lg text-sm font-medium transition-all h-10 px-4 shadow-sm hover:shadow-md bg-blue-500 text-black hover:bg-blue-600"
            disabled={isTransitioning}
          >
            Today
          </button>

          <button
            onClick={goToNextDay}
            className="inline-flex items-center justify-center rounded-lg text-sm font-medium transition-all hover:bg-blue-50 h-10 w-10 shadow-sm hover:shadow-md"
            disabled={isTransitioning}
          >
            <ChevronRight className="h-4 w-4" />
          </button>

          {onClose && (
            <button
              onClick={onClose}
              className="inline-flex items-center justify-center rounded-lg text-sm font-medium transition-all hover:bg-red-50 h-10 w-10 shadow-sm hover:shadow-md"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Calendar Container */}
      <div className="flex-1 relative overflow-hidden">
        {/* Previous Day - CLICKABLE */}
        <motion.div
          className="absolute left-0 top-0 bottom-0 w-[15%] overflow-hidden cursor-pointer"
          onClick={goToPreviousDay}
          whileHover={{ scale: 1.02 }}
          transition={{ duration: 0.2 }}
        >
          <div className="absolute inset-0 backdrop-blur-[2px] bg-white/40 z-10 pointer-events-none" />
          <div className="h-full scale-90 opacity-50">
            <div className="h-16 flex items-center justify-center bg-gradient-to-r from-blue-50 to-white shadow-sm">
              <p className="text-xs font-medium text-gray-600">
                {format(previousDay, "EEE, MMM d")}
              </p>
            </div>
            <DayView
              date={previousDay}
              tasks={previousDayTasks}
              currentTime={currentTime}
              onHourClick={() => {}}
              onShowMoreTasks={() => {}}
              isActive={false}
              targetTime={targetTime}
            />
          </div>
          <div className="absolute right-0 top-0 bottom-0 w-12 bg-gradient-to-l from-white to-transparent z-20 pointer-events-none" />
        </motion.div>

        {/* Current Day */}
        <div className="absolute left-[15%] right-[15%] top-0 bottom-0 z-30">
          <AnimatePresence mode="wait" custom={direction}>
            <motion.div
              key={currentDate.toISOString()}
              className="h-full relative"
              drag="x"
              dragConstraints={{ left: 0, right: 0 }}
              dragElastic={0.2}
              onDragEnd={handleDayChange}
              initial={{
                opacity: 0,
                x: direction === "next" ? 200 : -200,
                rotateY: direction === "next" ? 15 : -15,
              }}
              animate={{ opacity: 1, x: 0, rotateY: 0 }}
              exit={{
                opacity: 0,
                x: direction === "next" ? -200 : 200,
                rotateY: direction === "next" ? -15 : 15,
              }}
              transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
              style={{ transformStyle: "preserve-3d", perspective: 1200 }}
            >
              <div className="absolute inset-0 shadow-xl rounded-3xl pointer-events-none z-[-1]" />
              <div className="h-full bg-white rounded-3xl overflow-hidden shadow-lg">
                <DayView
                  date={currentDate}
                  tasks={currentDayTasks}
                  currentTime={currentTime}
                  onHourClick={handleHourClick}
                  onShowMoreTasks={handleShowMoreTasks}
                  isActive={true}
                  targetTime={targetTime}
                />
              </div>
            </motion.div>
          </AnimatePresence>

          {isTransitioning && (
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-blue-400/20 to-transparent z-40 pointer-events-none rounded-3xl"
              initial={{ x: direction === "next" ? "-100%" : "100%" }}
              animate={{ x: direction === "next" ? "100%" : "-100%" }}
              transition={{ duration: 0.6, ease: "linear" }}
            />
          )}
        </div>

        {/* Next Day - CLICKABLE */}
        <motion.div
          className="absolute right-0 top-0 bottom-0 w-[15%] overflow-hidden cursor-pointer"
          onClick={goToNextDay}
          whileHover={{ scale: 1.02 }}
          transition={{ duration: 0.2 }}
        >
          <div className="absolute inset-0 backdrop-blur-[2px] bg-white/40 z-10 pointer-events-none" />
          <div className="h-full scale-90 opacity-50">
            <div className="h-16 flex items-center justify-center bg-gradient-to-l from-blue-50 to-white shadow-sm">
              <p className="text-xs font-medium text-gray-600">
                {format(nextDay, "EEE, MMM d")}
              </p>
            </div>
            <DayView
              date={nextDay}
              tasks={nextDayTasks}
              currentTime={currentTime}
              onHourClick={() => {}}
              onShowMoreTasks={() => {}}
              isActive={false}
              targetTime={targetTime}
            />
          </div>
          <div className="absolute left-0 top-0 bottom-0 w-12 bg-gradient-to-r from-white to-transparent z-20 pointer-events-none" />
        </motion.div>
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

      {/* Task List Modal (for +N) */}
      <TaskListModal
        open={showTaskListModal}
        onOpenChange={setShowTaskListModal}
        tasks={selectedHourTasks}
      />
    </div>
  );
}
