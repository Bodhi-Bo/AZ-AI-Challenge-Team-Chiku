"use client";

import { useRef, useEffect, useState } from "react";
import { useCalendarStore } from "@/lib/stores/calendarStore";
import { useUIStore } from "@/lib/stores/uiStore";
import { format, addDays, subDays } from "date-fns";
import { X, ChevronLeft, ChevronRight } from "lucide-react";
import { motion } from "framer-motion";

const HOURS = Array.from({ length: 24 }, (_, i) => i); // 0-23 hours

export default function CalendarExpanded() {
  const { selectedDate, setSelectedDate, getTasksForDate } = useCalendarStore();
  const { setCalendarExpanded } = useUIStore();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Update current time every minute
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll to current hour
  useEffect(() => {
    if (scrollRef.current) {
      const currentHour = currentTime.getHours();
      const hourElement = scrollRef.current.children[
        currentHour
      ] as HTMLElement;
      if (hourElement) {
        hourElement.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
  }, [currentTime]);

  const previousDay = subDays(selectedDate, 1);
  const nextDay = addDays(selectedDate, 1);
  const todayTasks = getTasksForDate(selectedDate);

  const getTasksForHour = (hour: number) => {
    return todayTasks.filter((task: { startTime: Date }) => {
      const taskHour = task.startTime.getHours();
      return taskHour === hour;
    });
  };

  const getCategoryColor = (category?: string) => {
    switch (category) {
      case "study":
        return "from-primary-400 to-primary-600";
      case "break":
        return "from-accent-400 to-accent-600";
      case "class":
        return "from-blue-400 to-blue-600";
      case "deadline":
        return "from-red-400 to-red-600";
      default:
        return "from-secondary-400 to-secondary-600";
    }
  };

  return (
    <div className="h-full w-full bg-gradient-to-br from-secondary-50 to-primary-50/20 relative">
      {/* Header */}
      <div className="h-16 border-b border-secondary-200 bg-white/80 backdrop-blur-sm flex items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setSelectedDate(subDays(selectedDate, 1))}
            className="h-10 w-10 rounded-full hover:bg-secondary-100 flex items-center justify-center transition-colors"
          >
            <ChevronLeft className="h-5 w-5 text-secondary-600" />
          </button>

          <h2 className="text-xl font-bold text-secondary-900">
            {format(selectedDate, "EEEE, MMMM d")}
          </h2>

          <button
            onClick={() => setSelectedDate(addDays(selectedDate, 1))}
            className="h-10 w-10 rounded-full hover:bg-secondary-100 flex items-center justify-center transition-colors"
          >
            <ChevronRight className="h-5 w-5 text-secondary-600" />
          </button>
        </div>

        <button
          onClick={() => setCalendarExpanded(false)}
          className="h-10 w-10 rounded-full hover:bg-secondary-100 flex items-center justify-center transition-colors"
        >
          <X className="h-5 w-5 text-secondary-600" />
        </button>
      </div>

      {/* Horizontal Day View with Blur Edges */}
      <div className="h-[calc(100%-4rem)] relative">
        <div className="absolute inset-0 flex">
          {/* Previous Day - Blurred (3%) */}
          <div className="w-[3%] shrink-0 opacity-30 blur-sm bg-secondary-100 border-r border-secondary-200 flex flex-col items-center justify-center p-2">
            <p className="text-xs text-secondary-500 font-medium transform -rotate-90">
              {format(previousDay, "EEE")}
            </p>
          </div>

          {/* Current Day - Main View (94%) */}
          <div className="flex-1 overflow-y-auto" ref={scrollRef}>
            {HOURS.map((hour) => {
              const tasks = getTasksForHour(hour);
              const isCurrentHour =
                format(currentTime, "yyyy-MM-dd") ===
                  format(selectedDate, "yyyy-MM-dd") &&
                currentTime.getHours() === hour;

              return (
                <motion.div
                  key={hour}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: hour * 0.02 }}
                  className={`min-h-[120px] border-b border-secondary-200 p-4 relative ${
                    isCurrentHour ? "bg-primary-50/30" : "bg-white/50"
                  }`}
                >
                  {/* Hour Label */}
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-sm font-semibold text-secondary-700 w-16">
                      {format(new Date().setHours(hour, 0), "h:mm a")}
                    </span>
                    {isCurrentHour && (
                      <span className="text-xs px-2 py-1 rounded-full bg-primary-500 text-white font-medium">
                        Now
                      </span>
                    )}
                  </div>

                  {/* Tasks for this hour */}
                  <div className="space-y-2">
                    {tasks.map(
                      (task: {
                        id: string;
                        title: string;
                        startTime: Date;
                        endTime: Date;
                        category?: string;
                      }) => (
                        <motion.div
                          key={task.id}
                          initial={{ scale: 0.9, opacity: 0 }}
                          animate={{ scale: 1, opacity: 1 }}
                          className={`p-3 rounded-xl bg-gradient-to-r ${getCategoryColor(
                            task.category
                          )} text-white shadow-md`}
                        >
                          <p className="font-medium">{task.title}</p>
                          <p className="text-xs opacity-90 mt-1">
                            {format(task.startTime, "h:mm a")} -{" "}
                            {format(task.endTime, "h:mm a")}
                          </p>
                        </motion.div>
                      )
                    )}

                    {tasks.length === 0 && !isCurrentHour && (
                      <p className="text-sm text-secondary-400 italic">
                        No tasks
                      </p>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Next Day - Blurred (3%) */}
          <div className="w-[3%] shrink-0 opacity-30 blur-sm bg-secondary-100 border-l border-secondary-200 flex flex-col items-center justify-center p-2">
            <p className="text-xs text-secondary-500 font-medium transform -rotate-90">
              {format(nextDay, "EEE")}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
