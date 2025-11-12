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

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
      onClick={toggleCalendar}
      className="gradient-blue-white rounded-2xl p-6 shadow-md cursor-pointer hover:shadow-lg transition-all"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 rounded-xl gradient-blue-medium flex items-center justify-center shadow-sm">
            <Calendar className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="text-4xl font-bold text-blue-700 mb-1">
              {format(selectedDate, "d")}
            </div>
            <div className="text-sm font-medium text-blue-600">
              {format(selectedDate, "EEEE")}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {format(selectedDate, "MMMM yyyy")}
            </div>
          </div>
        </div>
        <ChevronRight className="h-5 w-5 text-blue-400 mt-2" />
      </div>
      
      <div className="pt-4 mt-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-blue-700">
              {todayTasks.length}
            </div>
            <div className="text-xs text-gray-500">
              {todayTasks.length === 1 ? "task" : "tasks"} today
            </div>
          </div>
          <div className="h-12 w-12 rounded-lg bg-blue-50 flex items-center justify-center">
            <div className="text-blue-600 font-semibold text-sm">
              {format(selectedDate, "MMM")}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
