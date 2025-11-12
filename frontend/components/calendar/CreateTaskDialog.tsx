"use client";

import { useState } from "react";
import { format } from "date-fns";
import { GraduationCap, Coffee, AlertCircle, Calendar } from "lucide-react";
import type { Task } from "@/lib/stores/calendarStore";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface CreateTaskDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedDate: Date;
  selectedHour: number;
  onCreateTask: (task: Omit<Task, "id">) => void;
}

type CategoryValue = Task["category"];

const categories: Array<{
  value: CategoryValue;
  label: string;
  icon: typeof GraduationCap;
  color: "violet" | "emerald" | "sky" | "rose" | "indigo" | "pink" | "slate";
}> = [
  {
    value: "study",
    label: "Study",
    icon: GraduationCap,
    color: "violet",
  },
  {
    value: "break",
    label: "Break",
    icon: Coffee,
    color: "emerald",
  },
  {
    value: "class",
    label: "Class",
    icon: Calendar,
    color: "sky",
  },
  {
    value: "deadline",
    label: "Deadline",
    icon: AlertCircle,
    color: "rose",
  },
  {
    value: "overtime",
    label: "Overtime",
    icon: AlertCircle,
    color: "rose",
  },
  {
    value: "meeting",
    label: "Meeting",
    icon: Calendar,
    color: "indigo",
  },
  {
    value: "personal",
    label: "Personal",
    icon: Calendar,
    color: "pink",
  },
  {
    value: "other",
    label: "Other",
    icon: Calendar,
    color: "slate",
  },
];

const categoryColorClasses = {
  violet: {
    selected: "bg-violet-100 shadow-md",
    unselected: "bg-white hover:bg-violet-50",
    icon: "text-violet-600",
    text: "text-violet-700",
  },
  emerald: {
    selected: "bg-emerald-100 shadow-md",
    unselected: "bg-white hover:bg-emerald-50",
    icon: "text-emerald-600",
    text: "text-emerald-700",
  },
  sky: {
    selected: "bg-sky-100 shadow-md",
    unselected: "bg-white hover:bg-sky-50",
    icon: "text-sky-600",
    text: "text-sky-700",
  },
  rose: {
    selected: "bg-rose-100 shadow-md",
    unselected: "bg-white hover:bg-rose-50",
    icon: "text-rose-600",
    text: "text-rose-700",
  },
  indigo: {
    selected: "bg-indigo-100 shadow-md",
    unselected: "bg-white hover:bg-indigo-50",
    icon: "text-indigo-600",
    text: "text-indigo-700",
  },
  pink: {
    selected: "bg-pink-100 shadow-md",
    unselected: "bg-white hover:bg-pink-50",
    icon: "text-pink-600",
    text: "text-pink-700",
  },
  slate: {
    selected: "bg-slate-100 shadow-md",
    unselected: "bg-white hover:bg-slate-50",
    icon: "text-slate-600",
    text: "text-slate-700",
  },
};

export default function CreateTaskDialog({
  open,
  onOpenChange,
  selectedDate,
  selectedHour,
  onCreateTask,
}: CreateTaskDialogProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [duration, setDuration] = useState("60");
  const [category, setCategory] = useState<CategoryValue>("study");

  console.log("Selected category:", category);

  const handleCategoryClick = (catValue: CategoryValue) => {
    setCategory(catValue);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim()) return;

    const startDate = new Date(selectedDate);
    startDate.setHours(selectedHour, 0, 0, 0);

    const endDate = new Date(startDate);
    endDate.setMinutes(endDate.getMinutes() + parseInt(duration));

    onCreateTask({
      title: title.trim(),
      description: description.trim(),
      startTime: startDate.toISOString(),
      endTime: endDate.toISOString(),
      category: category,
    });

    // Reset form
    setTitle("");
    setDescription("");
    setDuration("60");
    setCategory("study");
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[520px] bg-white shadow-xl">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-black">
            Add New Task
          </DialogTitle>
          <DialogDescription className="text-base text-gray-600 mt-2">
            {format(selectedDate, "EEEE, MMMM d")} at{" "}
            {format(new Date().setHours(selectedHour, 0, 0, 0), "h:mm a")}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6 mt-2">
          {/* Task Title */}
          <div className="space-y-2">
            <Label
              htmlFor="title"
              className="text-sm font-semibold text-gray-700"
            >
              Task Title *
            </Label>
            <Input
              id="title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Study Math Chapter 5"
              className="shadow-sm  border-0 overflow-hidden transition-shadow"
              autoFocus
              required
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label
              htmlFor="description"
              className="text-sm font-semibold text-gray-700"
            >
              Description (optional)
            </Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Add any notes or details about this task..."
              rows={3}
              className="resize-none shadow-sm  transition-shadow border-0"
            />
          </div>

          {/* Duration */}
          <div className="space-y-2">
            <Label
              htmlFor="duration"
              className="text-sm font-semibold text-gray-700"
            >
              Duration
            </Label>
            <Select value={duration} onValueChange={setDuration}>
              <SelectTrigger className="bg-white shadow-sm transition-shadow border-0">
                <SelectValue placeholder="Select duration" />
              </SelectTrigger>
              <SelectContent className="bg-white">
                <SelectItem value="15">15 minutes</SelectItem>
                <SelectItem value="30">30 minutes</SelectItem>
                <SelectItem value="45">45 minutes</SelectItem>
                <SelectItem value="60">1 hour</SelectItem>
                <SelectItem value="90">1.5 hours</SelectItem>
                <SelectItem value="120">2 hours</SelectItem>
                <SelectItem value="180">3 hours</SelectItem>
                <SelectItem value="240">4 hours</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Category */}
          <div className="space-y-3">
            <Label className="text-sm font-semibold text-gray-700">
              Category
            </Label>
            <div className="grid grid-cols-4 gap-3">
              {categories.map((cat) => {
                const Icon = cat.icon;
                const isSelected = category === cat.value;
                const colorClasses = categoryColorClasses[cat.color];

                return (
                  <button
                    key={cat.value}
                    type="button"
                    onClick={() => handleCategoryClick(cat.value)}
                    aria-pressed={isSelected}
                    className={`p-4 rounded-xl shadow-sm transition-all cursor-pointer ${
                      isSelected
                        ? colorClasses.selected
                        : colorClasses.unselected
                    }`}
                  >
                    <Icon
                      className={`w-6 h-6 mx-auto ${
                        isSelected ? colorClasses.icon : "text-gray-400"
                      }`}
                    />
                    <span
                      className={`block text-xs mt-2 font-medium ${
                        isSelected ? colorClasses.text : "text-gray-500"
                      }`}
                    >
                      {cat.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="shadow-sm hover:shadow-md transition-shadow"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!title.trim()}
              className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 shadow-md hover:shadow-lg transition-all"
            >
              Add Task
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
