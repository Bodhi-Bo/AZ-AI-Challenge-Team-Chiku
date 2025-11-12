"use client"

import { Button } from "@/components/ui/button"
import { ChevronLeft, ChevronRight, X } from "lucide-react"
import { format } from "date-fns"

interface CalendarHeaderProps {
  currentDate: Date
  onPreviousDay: () => void
  onNextDay: () => void
  onClose?: () => void
}

export default function CalendarHeader({
  currentDate,
  onPreviousDay,
  onNextDay,
  onClose,
}: CalendarHeaderProps) {
  return (
    <div className="sticky top-0 z-30 bg-gradient-to-r from-blue-500 to-blue-400 text-white px-6 py-4 shadow-lg">
      <div className="flex items-center justify-between">
        {/* Navigation Arrows */}
        <Button
          variant="ghost"
          size="icon"
          className="text-white hover:bg-white/20"
          onClick={onPreviousDay}
        >
          <ChevronLeft className="h-5 w-5" />
        </Button>

        {/* Current Date Display */}
        <h2 className="text-xl font-semibold">
          {format(currentDate, "EEEE, MMMM d")}
        </h2>

        {/* Next Day Arrow */}
        <Button
          variant="ghost"
          size="icon"
          className="text-white hover:bg-white/20"
          onClick={onNextDay}
        >
          <ChevronRight className="h-5 w-5" />
        </Button>

        {/* Close Button (if modal) */}
        {onClose && (
          <Button
            variant="ghost"
            size="icon"
            className="text-white hover:bg-white/20 ml-2"
            onClick={onClose}
          >
            <X className="h-5 w-5" />
          </Button>
        )}
      </div>
    </div>
  )
}

