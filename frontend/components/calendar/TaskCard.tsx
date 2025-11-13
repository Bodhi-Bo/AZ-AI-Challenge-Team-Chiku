"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { format, parseISO } from "date-fns";
import {
  Pencil,
  GraduationCap,
  Coffee,
  AlertCircle,
  Calendar,
  MoreVertical,
} from "lucide-react";
import type { Task } from "@/lib/stores/calendarStore";
import TaskDetailDialog from "./TaskDetailDialog";

interface TaskCardProps {
  task: Task;
  spanHours?: number;
  isStartHour?: boolean;
  isContinuation?: boolean;
  compact?: boolean;
}

const categoryConfig = {
  study: {
    icon: GraduationCap,
    leftBorder: "#a855f7", // purple-500
    bgColor: "#fefbff", // very light purple/white
    textColor: "text-purple-900",
    badgeColor: "bg-purple-100 text-purple-700",
    borderColor: "border-purple-200",
  },
  break: {
    icon: Coffee,
    leftBorder: "#22c55e", // green-500
    bgColor: "#f0fdf4", // green-50
    textColor: "text-green-900",
    badgeColor: "bg-green-100 text-green-700",
    borderColor: "border-green-200",
  },
  deadline: {
    icon: AlertCircle,
    leftBorder: "#ef4444", // red-500
    bgColor: "#fef2f2", // red-50
    textColor: "text-red-900",
    badgeColor: "bg-red-100 text-red-700",
    borderColor: "border-red-200",
  },
  class: {
    icon: Calendar,
    leftBorder: "#3b82f6", // blue-500
    bgColor: "#eff6ff", // blue-50
    textColor: "text-blue-900",
    badgeColor: "bg-blue-100 text-blue-700",
    borderColor: "border-blue-200",
  },
  overtime: {
    icon: AlertCircle,
    leftBorder: "#f87171", // red-400
    bgColor: "#fee2e2", // red-100
    textColor: "text-red-900",
    badgeColor: "bg-red-200 text-red-800",
    borderColor: "border-red-300",
  },
  meeting: {
    icon: Calendar,
    leftBorder: "#6366f1", // indigo-500
    bgColor: "#eef2ff", // indigo-50
    textColor: "text-indigo-900",
    badgeColor: "bg-indigo-100 text-indigo-700",
    borderColor: "border-indigo-200",
  },
  personal: {
    icon: Calendar,
    leftBorder: "#ec4899", // pink-500
    bgColor: "#fdf2f8", // pink-50
    textColor: "text-pink-900",
    badgeColor: "bg-pink-100 text-pink-700",
    borderColor: "border-pink-200",
  },
  other: {
    icon: Calendar,
    leftBorder: "#6b7280", // gray-500
    bgColor: "#f9fafb", // gray-50
    textColor: "text-gray-900",
    badgeColor: "bg-gray-100 text-gray-700",
    borderColor: "border-gray-200",
  },
};

export default function TaskCard({
  task,
  spanHours = 1,
  isStartHour = false,
  isContinuation = false,
  compact = false,
}: TaskCardProps) {
  const [showDetail, setShowDetail] = useState(false);
  const config = categoryConfig[task.category] || categoryConfig.other;
  const Icon = config.icon;
  const startTime = parseISO(task.startTime);
  const endTime = parseISO(task.endTime);

  const handleCardClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowDetail(true);
  };

  const handleEditClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    console.log("Edit task:", task.id);
  };

  // Continuation style - minimal indicator
  if (isContinuation) {
    return (
      <motion.div
        className={`relative rounded-lg cursor-pointer group h-16 border-l-4 ${config.borderColor}`}
        style={{
          backgroundColor: config.bgColor,
        }}
        whileHover={{ scale: 1.01 }}
        onClick={handleCardClick}
      >
        <div className="h-full flex items-center px-3">
          <div className="flex items-center gap-2 w-full">
            <div
              className="w-1 h-8 rounded-full"
              style={{ backgroundColor: config.leftBorder }}
            />
            <MoreVertical
              className={`w-4 h-4 ${config.textColor} opacity-40`}
            />
            <span className={`text-xs ${config.textColor} opacity-60 italic`}>
              {task.title} (continued)
            </span>
          </div>
        </div>

        <TaskDetailDialog
          task={task}
          open={showDetail}
          onOpenChange={setShowDetail}
        />
      </motion.div>
    );
  }

  // Calculate height for multi-hour tasks
  const cardHeight = spanHours > 1 ? `${spanHours * 80 - 16}px` : "auto";

  return (
    <>
      <motion.div
        className={`relative rounded-lg cursor-pointer group overflow-hidden border-l-4 ${config.borderColor}`}
        style={{
          backgroundColor: config.bgColor,
          minHeight: cardHeight,
          height: spanHours > 1 ? cardHeight : "auto",
        }}
        whileHover={{ scale: 1.01 }}
        transition={{ duration: 0.2 }}
        onClick={handleCardClick}
      >
        {/* Edit Button - Shows on hover */}
        <button
          onClick={handleEditClick}
          className="absolute top-2 right-2 p-1.5 rounded-lg bg-white/90 opacity-0 group-hover:opacity-100 transition-all hover:bg-white shadow-sm z-10"
        >
          <Pencil className="w-3.5 h-3.5 text-gray-600" />
        </button>

        <div className="p-3 h-full flex flex-col">
          {/* Header Section */}
          <div className="flex items-start gap-2 mb-2">
            {/* Icon */}
            <div
              className="p-1.5 rounded-lg"
              style={{
                backgroundColor: config.leftBorder + "20", // 20 = 12.5% opacity
              }}
            >
              <Icon className={`w-4 h-4 ${config.textColor}`} />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <h3
                className={`font-semibold ${config.textColor} text-sm ${
                  compact ? "text-xs" : ""
                } leading-tight`}
              >
                {task.title}
              </h3>
            </div>
          </div>

          {/* Time Display */}
          <p className="text-xs text-gray-600 font-medium ml-8 mb-2">
            {format(startTime, "h:mm a")} - {format(endTime, "h:mm a")}
          </p>

          {/* Description - Show if task spans multiple hours and not compact */}
          {!compact && spanHours > 1 && task.description && (
            <p className="text-xs text-gray-600 mt-2 ml-8 line-clamp-3 flex-1">
              {task.description}
            </p>
          )}

          {/* Category Badge */}
          <div className="mt-auto flex justify-end">
            <span
              className={`text-xs px-2.5 py-1 rounded-full ${config.badgeColor} font-medium shadow-sm`}
            >
              {task.category}
            </span>
          </div>
        </div>
      </motion.div>

      {/* Task Detail Dialog */}
      <TaskDetailDialog
        task={task}
        open={showDetail}
        onOpenChange={setShowDetail}
      />
    </>
  );
}
