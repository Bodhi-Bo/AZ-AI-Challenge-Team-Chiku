"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { Task } from "@/lib/stores/calendarStore";
import TaskDetailDialog from "./TaskDetailDialog";

interface TaskListModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tasks: Task[];
}

export default function TaskListModal({
  open,
  onOpenChange,
  tasks,
}: TaskListModalProps) {
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  // Reset index when modal opens by using the open state as the key
  const [currentIndex, setCurrentIndex] = useState(0);

  const handlePrevious = () => {
    setCurrentIndex((prev) => Math.max(0, prev - 1));
  };

  const handleNext = () => {
    setCurrentIndex((prev) => Math.min(tasks.length - 1, prev + 1));
  };

  if (tasks.length === 0) return null;

  const currentTask = tasks[currentIndex];

  return (
    <>
      <AnimatePresence>
        {open && (
          <>
            {/* Backdrop */}
            <motion.div
              className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => onOpenChange(false)}
            />

            {/* Modal - iOS style */}
            <div className="fixed inset-0 flex items-end justify-center z-50 pointer-events-none sm:items-center sm:p-4">
              <motion.div
                key={tasks[0]?.id || "modal"} // Reset state when tasks change
                className="bg-white rounded-t-3xl sm:rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden pointer-events-auto sm:max-h-[90vh] flex flex-col"
                initial={{ y: "100%", opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: "100%", opacity: 0 }}
                transition={{ type: "spring", damping: 25, stiffness: 200 }}
              >
                {/* Header - iOS style */}
                <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between bg-white">
                  <button
                    onClick={handlePrevious}
                    disabled={currentIndex === 0}
                    className="p-2 rounded-full hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                  >
                    <ChevronLeft className="w-5 h-5 text-gray-700" />
                  </button>

                  <div className="flex flex-col items-center">
                    <h2 className="text-lg font-semibold text-gray-900">
                      {tasks.length} {tasks.length === 1 ? "Event" : "Events"}
                    </h2>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {currentIndex + 1} of {tasks.length}
                    </p>
                  </div>

                  <button
                    onClick={handleNext}
                    disabled={currentIndex === tasks.length - 1}
                    className="p-2 rounded-full hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                  >
                    <ChevronRight className="w-5 h-5 text-gray-700" />
                  </button>
                </div>

                {/* Task Content */}
                <div className="flex-1 overflow-y-auto">
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={currentTask.id}
                      initial={{ opacity: 0, x: currentIndex > 0 ? 20 : -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: currentIndex > 0 ? -20 : 20 }}
                      transition={{ duration: 0.2 }}
                      className="p-6"
                    >
                      <div
                        className="bg-gray-50 rounded-2xl p-6 cursor-pointer hover:bg-gray-100 transition-colors border border-gray-200"
                        onClick={() => setSelectedTask(currentTask)}
                      >
                        <h3 className="text-xl font-bold text-gray-900 mb-2">
                          {currentTask.title}
                        </h3>
                        {currentTask.description && (
                          <p className="text-sm text-gray-600 mb-4">
                            {currentTask.description}
                          </p>
                        )}
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span className="capitalize px-3 py-1 rounded-full bg-white border border-gray-200">
                            {currentTask.category}
                          </span>
                        </div>
                      </div>
                    </motion.div>
                  </AnimatePresence>
                </div>

                {/* Dots Indicator - iOS style */}
                <div className="px-6 py-4 border-t border-gray-200 bg-white">
                  <div className="flex justify-center gap-2">
                    {tasks.map((_, index) => (
                      <button
                        key={index}
                        onClick={() => setCurrentIndex(index)}
                        className={`h-1.5 rounded-full transition-all ${
                          index === currentIndex
                            ? "bg-gray-900 w-6"
                            : "bg-gray-300 w-1.5 hover:bg-gray-400"
                        }`}
                      />
                    ))}
                  </div>
                </div>

                {/* Close Button */}
                <div className="px-6 pb-6">
                  <button
                    onClick={() => onOpenChange(false)}
                    className="w-full py-3 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-900 font-medium transition-colors"
                  >
                    Close
                  </button>
                </div>
              </motion.div>
            </div>
          </>
        )}
      </AnimatePresence>

      {/* Task Detail Dialog */}
      {selectedTask && (
        <TaskDetailDialog
          task={selectedTask}
          open={!!selectedTask}
          onOpenChange={(open) => !open && setSelectedTask(null)}
        />
      )}
    </>
  );
}
