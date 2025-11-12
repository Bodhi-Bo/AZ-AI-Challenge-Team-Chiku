"use client";

import { useCalendarStore } from "@/lib/stores/calendarStore";
import { useUIStore } from "@/lib/stores/uiStore";
import { format } from "date-fns";
import { Calendar, ChevronRight } from "lucide-react";
import { motion } from "framer-motion";

export default function CalendarWidget() {
  const { selectedDate, getTasksForDate } = useCalendarStore();
  const { toggleCalendar } = useUIStore();
  const todayTasks = getTasksForDate(selectedDate);
  const completedTasks = todayTasks.filter(
    (t: { completed?: boolean }) => t.completed
  ).length;

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      onClick={toggleCalendar}
      className="glass rounded-3xl p-6 cursor-pointer border border-white/20 shadow-xl transition-smooth hover:shadow-2xl"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Calendar Icon */}
          <div className="h-12 w-12 rounded-2xl gradient-bg-primary flex items-center justify-center">
            <Calendar className="h-6 w-6 text-white" />
          </div>

          {/* Date Info */}
          <div>
            <p className="text-2xl font-bold text-secondary-900">
              {format(selectedDate, "d")}
            </p>
            <p className="text-sm text-secondary-600">
              {format(selectedDate, "EEEE")}
            </p>
          </div>
        </div>

        {/* Task Summary */}
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm font-medium text-secondary-900">
              {todayTasks.length} tasks
            </p>
            <p className="text-xs text-secondary-500">
              {completedTasks} completed
            </p>
          </div>

          <ChevronRight className="h-5 w-5 text-secondary-400" />
        </div>
      </div>

      {/* Mini Progress Bar */}
      {todayTasks.length > 0 && (
        <div className="mt-4 h-2 bg-secondary-200 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{
              width: `${(completedTasks / todayTasks.length) * 100}%`,
            }}
            className="h-full gradient-bg-primary"
            transition={{ duration: 0.5 }}
          />
        </div>
      )}
    </motion.div>
  );
}
