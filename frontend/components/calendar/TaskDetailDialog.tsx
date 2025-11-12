"use client";

import { format, parseISO } from "date-fns";
import { Clock, Calendar as CalendarIcon, FileText, Tag } from "lucide-react";
import { useCalendarStore } from "@/lib/stores/calendarStore";
import type { Task } from "@/lib/stores/calendarStore";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";

interface TaskDetailDialogProps {
  task: Task;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const categoryConfig = {
  study: { label: "Study", gradient: "from-purple-400 to-purple-500" },
  break: { label: "Break", gradient: "from-green-400 to-green-500" },
  deadline: { label: "Deadline", gradient: "from-red-400 to-red-500" },
  class: { label: "Class", gradient: "from-blue-400 to-blue-500" },
  overtime: { label: "Overtime", gradient: "from-red-400 to-red-500" },
  meeting: { label: "Meeting", gradient: "from-indigo-400 to-indigo-500" },
  personal: { label: "Personal", gradient: "from-pink-400 to-pink-500" },
  other: { label: "Other", gradient: "from-gray-400 to-gray-500" },
};

export default function TaskDetailDialog({
  task,
  open,
  onOpenChange,
}: TaskDetailDialogProps) {
  const { deleteEvent } = useCalendarStore();
  const startTime = parseISO(task.startTime);
  const endTime = parseISO(task.endTime);
  const config = categoryConfig[task.category] || categoryConfig.other;

  const handleDelete = () => {
    if (confirm("Are you sure you want to delete this task?")) {
      deleteEvent(task.id);
      onOpenChange(false);
    }
  };

  const handleEdit = () => {
    // TODO: Implement edit functionality
    console.log("Edit task:", task.id);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px] p-0 overflow-hidden">
        {/* Gradient Header */}
        <div className={`bg-gradient-to-r ${config.gradient} p-6 text-white`}>
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold text-white">
              {task.title}
            </DialogTitle>
          </DialogHeader>
        </div>

        {/* Content Area */}
        <div className="p-6 space-y-4 bg-white">
          {/* Category Badge */}
          <div>
            <Label className="text-xs text-gray-500 uppercase tracking-wide">
              Category
            </Label>
            <div className="mt-1">
              <span className="inline-block px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-700">
                {config.label}
              </span>
            </div>
          </div>

          {/* Time */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
                <Clock className="w-4 h-4" />
                Time
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-base font-semibold text-gray-900">
                {format(startTime, "h:mm a")} - {format(endTime, "h:mm a")}
              </p>
            </CardContent>
          </Card>

          {/* Date */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
                <CalendarIcon className="w-4 h-4" />
                Date
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-base font-semibold text-gray-900">
                {format(startTime, "EEEE, MMMM d, yyyy")}
              </p>
            </CardContent>
          </Card>

          {/* Description */}
          {task.description && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  Description
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed text-gray-700">
                  {task.description}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Duration */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-500 flex items-center gap-2">
                <Tag className="w-4 h-4" />
                Duration
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-base font-semibold text-gray-900">
                {Math.round(
                  (endTime.getTime() - startTime.getTime()) / (1000 * 60)
                )}{" "}
                minutes
              </p>
            </CardContent>
          </Card>
        </div>

        <DialogFooter className="px-6 pb-6 gap-2">
          <Button
            variant="destructive"
            onClick={handleDelete}
            className="flex-1"
          >
            Delete
          </Button>
          <Button onClick={handleEdit} className="flex-1">
            Edit Task
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
