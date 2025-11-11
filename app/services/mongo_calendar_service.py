from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field
from pymongo import MongoClient
from bson import ObjectId
import os


class CalendarEvent(BaseModel):
    """Represents a calendar event with MongoDB support."""

    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    title: str
    date: str  # YYYY-MM-DD
    start_time: str  # HH:MM
    duration: int  # minutes
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class Reminder(BaseModel):
    """Represents a reminder with MongoDB support."""

    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    title: str
    reminder_datetime: str  # ISO format datetime string
    event_id: Optional[str] = None  # Link to event if this is event-based
    minutes_before_event: Optional[int] = None  # For event-based reminders
    priority: str = "normal"  # low, normal, high
    status: str = "pending"  # pending, completed, snoozed
    recurrence: Optional[str] = None  # once, daily, weekly, monthly
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class MongoCalendarService:
    """MongoDB-backed calendar service with semantic operations."""

    def __init__(self, connection_string: Optional[str] = None):
        """Initialize MongoDB connection."""
        if connection_string is None:
            connection_string = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")

        self.client = MongoClient(connection_string)
        self.db = self.client.calendar_assistant
        self.events = self.db.events
        self.reminders = self.db.reminders

        # Create indexes for efficient queries
        self.events.create_index([("user_id", 1), ("date", 1)])
        self.events.create_index([("user_id", 1), ("date", 1), ("start_time", 1)])
        self.reminders.create_index([("user_id", 1), ("reminder_datetime", 1)])
        self.reminders.create_index([("user_id", 1), ("status", 1)])

    def create_event(
        self,
        user_id: str,
        title: str,
        date: str,
        start_time: str,
        duration: int,
        description: Optional[str] = None,
    ) -> CalendarEvent:
        """Create a new calendar event."""
        event_dict = {
            "user_id": user_id,
            "title": title,
            "date": date,
            "start_time": start_time,
            "duration": duration,
            "description": description,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        result = self.events.insert_one(event_dict)
        event_dict["_id"] = str(result.inserted_id)

        return CalendarEvent(**event_dict)

    def get_user_events(self, user_id: str) -> List[CalendarEvent]:
        """Get all events for a user."""
        events = self.events.find({"user_id": user_id})
        return [
            CalendarEvent(**{**event, "_id": str(event["_id"])}) for event in events
        ]

    def get_events_by_date_range(
        self, user_id: str, start_date: str, end_date: Optional[str] = None
    ) -> List[CalendarEvent]:
        """Get events for a user within a date range."""
        if not end_date:
            end_date = start_date

        query = {"user_id": user_id, "date": {"$gte": start_date, "$lte": end_date}}

        events = self.events.find(query).sort([("date", 1), ("start_time", 1)])
        return [
            CalendarEvent(**{**event, "_id": str(event["_id"])}) for event in events
        ]

    def get_event(self, user_id: str, event_id: str) -> Optional[CalendarEvent]:
        """Get a specific event."""
        try:
            event = self.events.find_one(
                {"_id": ObjectId(event_id), "user_id": user_id}
            )
            if event:
                return CalendarEvent(**{**event, "_id": str(event["_id"])})
            return None
        except:
            return None

    def update_event(
        self,
        user_id: str,
        event_id: str,
        title: Optional[str] = None,
        date: Optional[str] = None,
        start_time: Optional[str] = None,
        duration: Optional[int] = None,
        description: Optional[str] = None,
    ) -> Optional[CalendarEvent]:
        """Update an existing event."""
        try:
            update_fields: dict = {"updated_at": datetime.now()}

            if title is not None:
                update_fields["title"] = title
            if date is not None:
                update_fields["date"] = date
            if start_time is not None:
                update_fields["start_time"] = start_time
            if duration is not None:
                update_fields["duration"] = duration
            if description is not None:
                update_fields["description"] = description

            result = self.events.find_one_and_update(
                {"_id": ObjectId(event_id), "user_id": user_id},
                {"$set": update_fields},
                return_document=True,
            )

            if result:
                return CalendarEvent(**{**result, "_id": str(result["_id"])})
            return None
        except:
            return None

    def delete_event(self, user_id: str, event_id: str) -> bool:
        """Delete an event."""
        try:
            result = self.events.delete_one(
                {"_id": ObjectId(event_id), "user_id": user_id}
            )
            return result.deleted_count > 0
        except:
            return False

    def get_events_on_date(self, user_id: str, date: str) -> List[CalendarEvent]:
        """Get all events for a specific date."""
        return self.get_events_by_date_range(user_id, date, date)

    def find_available_slots(
        self,
        user_id: str,
        date: str,
        duration_minutes: int,
        work_hours: tuple = (9, 17),
    ) -> List[dict]:
        """
        Find available time slots on a given date.
        Returns list of available slots as {start_time: str, end_time: str}.
        """
        events = self.get_events_on_date(user_id, date)

        # Create list of busy periods
        busy_periods = []
        for event in events:
            start_hour, start_min = map(int, event.start_time.split(":"))
            start_minutes = start_hour * 60 + start_min
            end_minutes = start_minutes + event.duration
            busy_periods.append((start_minutes, end_minutes))

        # Sort busy periods
        busy_periods.sort()

        # Find gaps
        available_slots = []
        work_start = work_hours[0] * 60  # 9am in minutes
        work_end = work_hours[1] * 60  # 5pm in minutes

        current_time = work_start

        for busy_start, busy_end in busy_periods:
            if busy_start - current_time >= duration_minutes:
                # Found a gap
                available_slots.append(
                    {
                        "start_time": f"{current_time // 60:02d}:{current_time % 60:02d}",
                        "end_time": f"{busy_start // 60:02d}:{busy_start % 60:02d}",
                        "duration_minutes": busy_start - current_time,
                    }
                )
            current_time = max(current_time, busy_end)

        # Check final slot until end of work day
        if work_end - current_time >= duration_minutes:
            available_slots.append(
                {
                    "start_time": f"{current_time // 60:02d}:{current_time % 60:02d}",
                    "end_time": f"{work_end // 60:02d}:{work_end % 60:02d}",
                    "duration_minutes": work_end - current_time,
                }
            )

        return available_slots

    def is_time_available(
        self, user_id: str, date: str, start_time: str, duration: int
    ) -> bool:
        """Check if a specific time slot is available."""
        events = self.get_events_on_date(user_id, date)

        # Parse proposed time
        proposed_hour, proposed_min = map(int, start_time.split(":"))
        proposed_start = proposed_hour * 60 + proposed_min
        proposed_end = proposed_start + duration

        # Check for conflicts
        for event in events:
            event_hour, event_min = map(int, event.start_time.split(":"))
            event_start = event_hour * 60 + event_min
            event_end = event_start + event.duration

            # Check if times overlap
            if not (proposed_end <= event_start or proposed_start >= event_end):
                return False

        return True

    # ================== REMINDER METHODS ==================

    def create_reminder(
        self,
        user_id: str,
        title: str,
        reminder_datetime: str,
        event_id: Optional[str] = None,
        priority: str = "normal",
        recurrence: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Reminder:
        """Create a new reminder."""
        reminder_dict = {
            "user_id": user_id,
            "title": title,
            "reminder_datetime": reminder_datetime,
            "event_id": event_id,
            "minutes_before_event": None,
            "priority": priority,
            "status": "pending",
            "recurrence": recurrence,
            "notes": notes,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        result = self.reminders.insert_one(reminder_dict)
        reminder_dict["_id"] = str(result.inserted_id)

        return Reminder(**reminder_dict)

    def create_reminder_for_event(
        self,
        user_id: str,
        event_id: str,
        minutes_before: int,
        title: Optional[str] = None,
        priority: str = "normal",
    ) -> Optional[Reminder]:
        """Create a reminder X minutes before an event."""
        # Get the event
        event = self.get_event(user_id, event_id)
        if not event:
            return None

        # Calculate reminder time
        event_datetime = datetime.strptime(
            f"{event.date} {event.start_time}", "%Y-%m-%d %H:%M"
        )
        reminder_datetime = event_datetime - timedelta(minutes=minutes_before)

        # Use event title if no custom title provided
        if not title:
            title = f"Reminder: {event.title}"

        reminder_dict = {
            "user_id": user_id,
            "title": title,
            "reminder_datetime": reminder_datetime.isoformat(),
            "event_id": event_id,
            "minutes_before_event": minutes_before,
            "priority": priority,
            "status": "pending",
            "recurrence": None,
            "notes": f"Reminder for event: {event.title}",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        result = self.reminders.insert_one(reminder_dict)
        reminder_dict["_id"] = str(result.inserted_id)

        return Reminder(**reminder_dict)

    def get_upcoming_reminders(
        self, user_id: str, hours_ahead: int = 24
    ) -> List[Reminder]:
        """Get upcoming reminders within the next X hours."""
        now = datetime.now()
        future = now + timedelta(hours=hours_ahead)

        query = {
            "user_id": user_id,
            "status": "pending",
            "reminder_datetime": {"$gte": now.isoformat(), "$lte": future.isoformat()},
        }

        reminders = self.reminders.find(query).sort("reminder_datetime", 1)
        return [
            Reminder(**{**reminder, "_id": str(reminder["_id"])})
            for reminder in reminders
        ]

    def get_pending_reminders(self, user_id: str) -> List[Reminder]:
        """Get all pending reminders for a user."""
        query = {"user_id": user_id, "status": "pending"}

        reminders = self.reminders.find(query).sort("reminder_datetime", 1)
        return [
            Reminder(**{**reminder, "_id": str(reminder["_id"])})
            for reminder in reminders
        ]

    def mark_reminder_completed(self, user_id: str, reminder_id: str) -> bool:
        """Mark a reminder as completed."""
        try:
            result = self.reminders.find_one_and_update(
                {"_id": ObjectId(reminder_id), "user_id": user_id},
                {"$set": {"status": "completed", "updated_at": datetime.now()}},
                return_document=True,
            )
            return result is not None
        except:
            return False

    def snooze_reminder(
        self, user_id: str, reminder_id: str, snooze_minutes: int
    ) -> Optional[Reminder]:
        """Snooze a reminder by X minutes."""
        try:
            reminder = self.reminders.find_one(
                {"_id": ObjectId(reminder_id), "user_id": user_id}
            )
            if not reminder:
                return None

            current_time = datetime.fromisoformat(reminder["reminder_datetime"])
            new_time = current_time + timedelta(minutes=snooze_minutes)

            result = self.reminders.find_one_and_update(
                {"_id": ObjectId(reminder_id), "user_id": user_id},
                {
                    "$set": {
                        "reminder_datetime": new_time.isoformat(),
                        "status": "snoozed",
                        "updated_at": datetime.now(),
                    }
                },
                return_document=True,
            )

            if result:
                return Reminder(**{**result, "_id": str(result["_id"])})
            return None
        except:
            return None

    def delete_reminder(self, user_id: str, reminder_id: str) -> bool:
        """Delete a reminder."""
        try:
            result = self.reminders.delete_one(
                {"_id": ObjectId(reminder_id), "user_id": user_id}
            )
            return result.deleted_count > 0
        except:
            return False


# Global instance
calendar_service = MongoCalendarService()
