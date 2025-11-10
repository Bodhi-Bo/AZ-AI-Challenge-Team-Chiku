"use client";

import { useRef, useState } from "react";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import type {
  DateSelectArg,
  EventClickArg,
  EventDropArg,
} from "@fullcalendar/core";
import { useStore } from "@/lib/store";
import type { CalendarEvent } from "@/types";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Trash2 } from "lucide-react";
import { format } from "date-fns";

export default function CalendarView() {
  const { events, addEvent, updateEvent, deleteEvent } = useStore();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingEvent, setEditingEvent] = useState<CalendarEvent | null>(null);
  const [eventTitle, setEventTitle] = useState("");
  const [eventDescription, setEventDescription] = useState("");
  const [eventStart, setEventStart] = useState<Date | null>(null);
  const [eventEnd, setEventEnd] = useState<Date | null>(null);
  const calendarRef = useRef<FullCalendar>(null);

  // Convert events to FullCalendar format
  const calendarEvents = events.map((event) => ({
    id: event.id,
    title: event.title,
    start: event.start.toISOString(),
    end: event.end.toISOString(),
    backgroundColor: getEventColor(event.category),
    borderColor: getEventColor(event.category),
    extendedProps: {
      description: event.description,
      category: event.category,
    },
  }));

  function getEventColor(category?: string): string {
    switch (category) {
      case "class":
        return "#3B82F6"; // Blue
      case "study":
        return "#10B981"; // Green
      case "break":
        return "#F59E0B"; // Orange
      case "deadline":
        return "#EF4444"; // Red
      default:
        return "#6366F1"; // Indigo
    }
  }

  const handleDateSelect = (selectInfo: DateSelectArg) => {
    setEventStart(selectInfo.start);
    setEventEnd(selectInfo.end);
    setEventTitle("");
    setEventDescription("");
    setEditingEvent(null);
    setIsDialogOpen(true);
  };

  const handleEventClick = (clickInfo: EventClickArg) => {
    const event = events.find((e) => e.id === clickInfo.event.id);
    if (event) {
      setEditingEvent(event);
      setEventTitle(event.title);
      setEventDescription(event.description || "");
      setEventStart(event.start);
      setEventEnd(event.end);
      setIsDialogOpen(true);
    }
  };

  const handleEventDrop = (dropInfo: EventDropArg) => {
    const event = events.find((e) => e.id === dropInfo.event.id);
    if (event) {
      updateEvent(event.id, {
        start: dropInfo.event.start!,
        end: dropInfo.event.end || dropInfo.event.start!,
      });
    }
  };

  const handleSave = () => {
    if (!eventTitle.trim() || !eventStart || !eventEnd) {
      return;
    }

    if (editingEvent) {
      updateEvent(editingEvent.id, {
        title: eventTitle,
        description: eventDescription,
        start: eventStart,
        end: eventEnd,
      });
    } else {
      const newEvent: CalendarEvent = {
        id: Date.now().toString(),
        title: eventTitle,
        description: eventDescription,
        start: eventStart,
        end: eventEnd,
        category: "other",
      };
      addEvent(newEvent);
    }

    setIsDialogOpen(false);
    setEditingEvent(null);
    setEventTitle("");
    setEventDescription("");
  };

  const handleDelete = () => {
    if (editingEvent) {
      deleteEvent(editingEvent.id);
      setIsDialogOpen(false);
      setEditingEvent(null);
    }
  };

  // Highlight current time - FullCalendar handles this automatically with nowIndicator
  // No need for manual updates

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-900 overflow-hidden">
      {/* Header */}
      <div className="px-8 py-6 border-b border-gray-100 dark:border-gray-800 shrink-0">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
          Schedule
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Manage your tasks and events
        </p>
      </div>

      {/* Calendar Container - Scrollable */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="max-w-full">
          <FullCalendar
            ref={calendarRef}
            plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
            initialView="timeGridWeek"
            headerToolbar={{
              left: "prev,next today",
              center: "title",
              right: "dayGridMonth,timeGridWeek,timeGridDay",
            }}
            events={calendarEvents}
            editable={true}
            droppable={true}
            selectable={true}
            selectMirror={true}
            dayMaxEvents={true}
            weekends={true}
            select={handleDateSelect}
            eventClick={handleEventClick}
            eventDrop={handleEventDrop}
            height="auto"
            slotMinTime="06:00:00"
            slotMaxTime="24:00:00"
            allDaySlot={false}
            nowIndicator={true}
            eventDisplay="block"
            eventTimeFormat={{
              hour: "numeric",
              minute: "2-digit",
              meridiem: "short",
            }}
          />
        </div>
      </div>

      {/* Event Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>
              {editingEvent ? "Edit Event" : "Create New Event"}
            </DialogTitle>
            <DialogDescription>
              {editingEvent
                ? "Update the event details below."
                : "Fill in the details to create a new calendar event."}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Title</label>
              <Input
                value={eventTitle}
                onChange={(e) => setEventTitle(e.target.value)}
                placeholder="Event title"
                className="text-base"
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                Description
              </label>
              <Textarea
                value={eventDescription}
                onChange={(e) => setEventDescription(e.target.value)}
                placeholder="Add a description..."
                rows={3}
                className="text-base"
              />
            </div>

            {eventStart && eventEnd && (
              <div className="space-y-2">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Start
                  </label>
                  <Input
                    type="datetime-local"
                    value={format(eventStart, "yyyy-MM-dd'T'HH:mm")}
                    onChange={(e) => setEventStart(new Date(e.target.value))}
                    className="text-base"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">End</label>
                  <Input
                    type="datetime-local"
                    value={format(eventEnd, "yyyy-MM-dd'T'HH:mm")}
                    onChange={(e) => setEventEnd(new Date(e.target.value))}
                    className="text-base"
                  />
                </div>
              </div>
            )}
          </div>

          <DialogFooter className="flex justify-between">
            <div>
              {editingEvent && (
                <Button
                  variant="destructive"
                  onClick={handleDelete}
                  className="mr-auto"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </Button>
              )}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={!eventTitle.trim()}>
                {editingEvent ? "Update" : "Create"}
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <style jsx global>{`
        .fc {
          font-family: inherit;
        }
        .fc .fc-toolbar-title {
          font-size: 1.5rem;
          font-weight: 600;
          color: #111827;
        }
        .dark .fc .fc-toolbar-title {
          color: #f3f4f6;
        }
        .fc .fc-button {
          background: white;
          border: 1px solid #e5e7eb;
          color: #374151;
          border-radius: 0.5rem;
          padding: 0.5rem 1rem;
          font-weight: 500;
          transition: all 0.2s;
        }
        .fc .fc-button:hover {
          background: #f9fafb;
          border-color: #d1d5db;
        }
        .fc .fc-button-primary:not(:disabled).fc-button-active {
          background: #4f46e5;
          border-color: #4f46e5;
          color: white;
        }
        .fc .fc-col-header-cell {
          padding: 1rem 0.5rem;
          font-weight: 600;
          font-size: 0.875rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: #6b7280;
        }
        .fc .fc-daygrid-day-number,
        .fc .fc-timegrid-slot-label {
          padding: 0.5rem;
          color: #374151;
          font-weight: 500;
        }
        .dark .fc .fc-daygrid-day-number,
        .dark .fc .fc-timegrid-slot-label {
          color: #d1d5db;
        }
        .fc .fc-event {
          border-radius: 0.5rem;
          padding: 0.25rem 0.5rem;
          font-weight: 500;
          border: none;
          box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        }
        .fc .fc-event-title {
          font-size: 0.875rem;
        }
        .fc .fc-timegrid-now-indicator-line {
          border-color: #ef4444;
          border-width: 2px;
        }
        .fc .fc-day-today {
          background-color: rgba(79, 70, 229, 0.05) !important;
        }
        .fc .fc-scrollgrid {
          border-color: #f3f4f6;
        }
        .dark .fc .fc-scrollgrid {
          border-color: #374151;
        }
      `}</style>
    </div>
  );
}
