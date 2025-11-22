"use client";

import { format, isSameDay, parseISO } from "date-fns";
import { motion } from "framer-motion";
import { useEffect, useRef } from "react";
import type { Task } from "@/lib/stores/calendarStore";
import TaskCard from "./TaskCard";
import { convertToMST } from "@/lib/timezone";

interface DayViewProps {
  date: Date;
  tasks: Task[];
  currentTime: Date;
  onHourClick: (hour: number) => void;
  onShowMoreTasks: (tasks: Task[]) => void;
  isActive: boolean;
  targetTime?: Date; // Optional target time to scroll to
}

export default function DayView({
  date,
  tasks,
  currentTime,
  onHourClick,
  onShowMoreTasks,
  isActive,
  targetTime,
}: DayViewProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const hours = Array.from({ length: 24 }, (_, i) => i);
  const hourHeight = 80; // Height of each hour slot in pixels

  // Convert all times to MST
  const mstDate = convertToMST(date);
  const mstCurrentTime = convertToMST(currentTime);

  // Check if current time is today
  const isToday = isSameDay(mstDate, mstCurrentTime);

  // Use targetTime if provided, otherwise use currentTime (convert to MST)
  const timeToScrollTo = targetTime ? convertToMST(targetTime) : mstCurrentTime;
  const targetHour = timeToScrollTo.getHours();
  const targetMinute = timeToScrollTo.getMinutes();

  const currentHour = mstCurrentTime.getHours();
  const currentMinute = mstCurrentTime.getMinutes();

  // Custom smooth scroll function with adjustable duration and advanced easing
  const smoothScrollTo = (
    element: HTMLElement,
    targetPosition: number,
    duration: number
  ) => {
    const startPosition = element.scrollTop;
    const distance = targetPosition - startPosition;
    const startTime = performance.now();

    // Advanced easing function - smoother than cubic
    const easeInOutQuart = (t: number): number => {
      return t < 0.5 ? 8 * t * t * t * t : 1 - Math.pow(-2 * t + 2, 4) / 2;
    };

    const animate = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easeProgress = easeInOutQuart(progress);

      element.scrollTop = startPosition + distance * easeProgress;

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  };

  // Scroll to target time on mount (only for active view)
  useEffect(() => {
    if (isActive && scrollContainerRef.current) {
      // Calculate the exact position of target time
      const position = (targetHour + targetMinute / 60) * hourHeight;

      // Scroll after a brief delay to ensure rendering is complete
      setTimeout(() => {
        if (scrollContainerRef.current) {
          // Scroll to position with the target time centered in view
          const containerHeight = scrollContainerRef.current.clientHeight;
          const scrollTop = position - containerHeight / 2 + hourHeight / 2;

          // Use smooth custom scroll animation with longer duration for more visible scroll
          smoothScrollTo(
            scrollContainerRef.current,
            Math.max(0, scrollTop),
            300
          );
        }
      }, 400);
    }
  }, [isActive, targetHour, targetMinute, hourHeight]);

  // Calculate which hours a task occupies
  const getTaskSpan = (task: Task) => {
    const startTime = convertToMST(parseISO(task.startTime));
    const endTime = convertToMST(parseISO(task.endTime));
    const startHour = startTime.getHours();
    const startMinute = startTime.getMinutes();
    const endHour = endTime.getHours();
    const endMinute = endTime.getMinutes();

    // Calculate the actual hours this task spans
    const hoursSpanned: number[] = [];
    for (let h = startHour; h <= endHour; h++) {
      // Include the hour if:
      // - It's the start hour
      // - It's a middle hour
      // - It's the end hour and there are minutes past the hour
      if (h === startHour || h < endHour || (h === endHour && endMinute > 0)) {
        hoursSpanned.push(h);
      }
    }

    return {
      startHour,
      startMinute,
      endHour,
      endMinute,
      hoursSpanned,
      spanCount: hoursSpanned.length,
    };
  };

  // Get all tasks that are visible at this hour (including spanning tasks)
  const getTasksAtHour = (hour: number) => {
    return tasks.filter((task) => {
      const span = getTaskSpan(task);
      return span.hoursSpanned.includes(hour);
    });
  };

  // Get tasks that START at this hour
  const getTasksStartingAtHour = (hour: number) => {
    return tasks.filter((task) => {
      const taskStart = convertToMST(parseISO(task.startTime));
      return taskStart.getHours() === hour;
    });
  };

  // Calculate position of current time indicator based on hour slots
  const getCurrentTimePosition = () => {
    if (!isToday) return null;
    // Each hour slot is 80px, calculate exact position
    const hourPosition = currentHour * hourHeight;
    const minuteOffset = (currentMinute / 60) * hourHeight;
    return hourPosition + minuteOffset;
  };

  const currentTimePosition = getCurrentTimePosition();

  return (
    <div
      ref={scrollContainerRef}
      className="h-full overflow-y-auto overflow-x-hidden relative scroll-smooth"
    >
      {/* Current Time Indicator */}
      {isToday && currentTimePosition !== null && (
        <motion.div
          className="absolute left-0 right-0 z-50 flex items-center pointer-events-none"
          style={{ top: `${currentTimePosition}px` }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="w-3 h-3 rounded-full bg-red-500 ml-2 shadow-md z-10" />
          <div className="flex-1 h-[2px] bg-red-500 shadow-sm" />
          <span className="text-xs font-semibold text-red-500 mr-4 bg-white px-2 py-1 rounded-md shadow-md">
            {format(mstCurrentTime, "h:mm a")} MST
          </span>
        </motion.div>
      )}

      {/* Hours Grid */}
      <div className="relative">
        {hours.map((hour) => {
          const tasksAtHour = getTasksAtHour(hour);
          const tasksStartingHere = getTasksStartingAtHour(hour);

          // Determine if this hour is just a "continuation" row
          const isContinuationOnly =
            tasksAtHour.length > 0 && tasksStartingHere.length === 0;

          return (
            <div
              key={hour}
              id={`hour-${hour}`}
              className="relative min-h-[80px] flex shadow-sm"
              style={{
                background:
                  hour % 2 === 0 ? "white" : "rgba(239, 246, 255, 0.3)",
              }}
            >
              {/* Time Label */}
              <div className="w-24 flex-shrink-0 p-3 text-right bg-gradient-to-r from-blue-50/50 to-transparent">
                <span className="text-sm font-medium text-gray-600">
                  {(() => {
                    const hourDate = new Date();
                    hourDate.setHours(hour, 0, 0, 0);
                    return format(convertToMST(hourDate), "h:mm a");
                  })()}
                </span>
              </div>

              {/* Task Area */}
              <div
                className="flex-1 relative p-2"
                style={{ paddingRight: isActive ? "0" : "0.5rem" }}
              >
                {/* Show tasks that START at this hour */}
                {tasksStartingHere.length > 0 ? (
                  <div className="space-y-2">
                    {tasksStartingHere.slice(0, 2).map((task) => {
                      const span = getTaskSpan(task);
                      return (
                        <div key={task.id}>
                          <TaskCard
                            task={task}
                            spanHours={span.spanCount}
                            isStartHour={true}
                          />
                        </div>
                      );
                    })}
                    {/* Show +N indicator if there are more than 2 tasks */}
                    {tasksStartingHere.length > 2 && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onShowMoreTasks(tasksStartingHere);
                        }}
                        className="w-full py-2 px-3 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium transition-colors border border-gray-200"
                      >
                        +{tasksStartingHere.length - 2} more
                      </button>
                    )}
                  </div>
                ) : isContinuationOnly ? (
                  // Show continuation indicators for tasks that span through this hour
                  <div className="space-y-2">
                    {tasksAtHour.slice(0, 2).map((task) => (
                      <TaskCard
                        key={task.id}
                        task={task}
                        isContinuation={true}
                      />
                    ))}
                    {tasksAtHour.length > 2 && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onShowMoreTasks(tasksAtHour);
                        }}
                        className="w-full py-2 px-3 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium transition-colors border border-gray-200"
                      >
                        +{tasksAtHour.length - 2} more
                      </button>
                    )}
                  </div>
                ) : (
                  // Empty slot - clickable to add task
                  <div
                    className={`h-full flex items-center justify-center ${
                      isActive
                        ? "cursor-pointer hover:bg-blue-50/50 rounded-lg transition-all"
                        : ""
                    }`}
                    onClick={() => isActive && onHourClick(hour)}
                  >
                    {isActive && (
                      <span className="text-xs text-gray-400 italic opacity-0 hover:opacity-100 transition-opacity">
                        Click to add task
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Right margin for adding events - 20px clickable area */}
              {isActive && (
                <div
                  className="flex-shrink-0 cursor-pointer hover:bg-blue-50/50 transition-colors group relative"
                  style={{ width: "20px" }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onHourClick(hour);
                  }}
                  title="Click to add event"
                >
                  <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="w-1 h-8 bg-blue-400 rounded-full" />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
