"use client"

import { useState } from "react"
import { format } from "date-fns"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import type { Task } from "@/lib/stores/calendarStore"

interface CreateTaskDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  selectedDate: Date
  selectedHour: number
  onCreateTask: (task: Omit<Task, "id">) => void
}

type TaskCategory = "study" | "break" | "class" | "deadline" | "other"

export default function CreateTaskDialog({
  open,
  onOpenChange,
  selectedDate,
  selectedHour,
  onCreateTask,
}: CreateTaskDialogProps) {
  const [title, setTitle] = useState("")
  const [duration, setDuration] = useState("1")
  const [category, setCategory] = useState<TaskCategory>("study")

  const formatTime = (hour: number) => {
    const date = new Date()
    date.setHours(hour, 0, 0, 0)
    return format(date, "h:mm a")
  }

  const handleCreateTask = () => {
    if (!title.trim()) return

    const startTime = new Date(selectedDate)
    startTime.setHours(selectedHour, 0, 0, 0)

    const endTime = new Date(startTime)
    endTime.setHours(selectedHour + parseFloat(duration), 0, 0, 0)

    onCreateTask({
      title: title.trim(),
      startTime,
      endTime,
      category,
      completed: false,
    })

    // Reset form
    setTitle("")
    setDuration("1")
    setCategory("study")
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Task</DialogTitle>
          <DialogDescription>
            {format(selectedDate, "EEEE, MMMM d")} at {formatTime(selectedHour)}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Title Input */}
          <div>
            <label className="text-sm font-medium mb-2 block">Task Title</label>
            <Input
              placeholder="Task title..."
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              autoFocus
              onKeyDown={(e) => {
                if (e.key === "Enter" && title.trim()) {
                  handleCreateTask()
                }
              }}
            />
          </div>

          {/* Duration Select */}
          <div>
            <label className="text-sm font-medium mb-2 block">Duration</label>
            <Select value={duration} onChange={(e) => setDuration(e.target.value)}>
              <option value="0.5">30 minutes</option>
              <option value="1">1 hour</option>
              <option value="1.5">1.5 hours</option>
              <option value="2">2 hours</option>
              <option value="3">3 hours</option>
              <option value="4">4 hours</option>
            </Select>
          </div>

          {/* Category Selection */}
          <div>
            <label className="text-sm font-medium mb-2 block">Category</label>
            <div className="flex gap-2 flex-wrap">
              <Badge
                className="cursor-pointer"
                variant={category === "study" ? "default" : "outline"}
                onClick={() => setCategory("study")}
              >
                📚 Study
              </Badge>
              <Badge
                className="cursor-pointer"
                variant={category === "break" ? "default" : "outline"}
                onClick={() => setCategory("break")}
              >
                ☕ Break
              </Badge>
              <Badge
                className="cursor-pointer"
                variant={category === "class" ? "default" : "outline"}
                onClick={() => setCategory("class")}
              >
                🎓 Class
              </Badge>
              <Badge
                className="cursor-pointer"
                variant={category === "deadline" ? "default" : "outline"}
                onClick={() => setCategory("deadline")}
              >
                ⏰ Deadline
              </Badge>
              <Badge
                className="cursor-pointer"
                variant={category === "other" ? "default" : "outline"}
                onClick={() => setCategory("other")}
              >
                📝 Other
              </Badge>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleCreateTask} disabled={!title.trim()}>
            Add Task
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

