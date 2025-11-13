"""
Calendar service using Beanie ODM for MongoDB operations.
Provides semantic calendar and reminder management.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from beanie import PydanticObjectId

from app.models.db.calendar_event import CalendarEvent
from app.models.db.reminder import Reminder
from app.utils.embedding_util import generate_embedding


class MongoCalendarService:
    """MongoDB-backed calendar service using Beanie ODM."""

    # ================== EVENT METHODS ==================

    async def create_event(
        self,
        user_id: str,
        title: str,
        date: str,
        start_time: str,
        duration: int,
        description: Optional[str] = None,
    ) -> CalendarEvent:
        """Create a new calendar event."""
        # Parse date and time strings into a datetime object
        event_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")

        # Generate embedding for semantic search
        title_embedding = generate_embedding(title)

        event = CalendarEvent(
            user_id=user_id,
            title=title,
            event_datetime=event_datetime,
            duration=duration,
            description=description,
            title_embedding=title_embedding,
        )
        await event.insert()
        return event

    async def get_user_events(self, user_id: str) -> List[CalendarEvent]:
        """Get all events for a user."""
        events = await CalendarEvent.find(CalendarEvent.user_id == user_id).to_list()
        return events

    async def get_events_by_date_range(
        self, user_id: str, start_date: str, end_date: Optional[str] = None
    ) -> List[CalendarEvent]:
        """Get events for a user within a date range."""
        if not end_date:
            end_date = start_date

        # Parse dates to datetime objects (start of day and end of day)
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59
        )

        events = (
            await CalendarEvent.find(
                CalendarEvent.user_id == user_id,
                CalendarEvent.event_datetime >= start_dt,
                CalendarEvent.event_datetime <= end_dt,
            )
            .sort("event_datetime")
            .to_list()
        )

        return events

    async def get_event(self, user_id: str, event_id: str) -> Optional[CalendarEvent]:
        """Get a specific event."""
        try:
            event = await CalendarEvent.get(PydanticObjectId(event_id))
            if event and event.user_id == user_id:
                return event
            return None
        except Exception:
            return None

    async def update_event(
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
            event = await CalendarEvent.get(PydanticObjectId(event_id))
            if not event or event.user_id != user_id:
                return None

            update_data: Dict[str, Any] = {"updated_at": datetime.utcnow()}

            # If date or start_time is being updated, we need to update event_datetime
            if date is not None or start_time is not None:
                # Use existing values if not updating
                current_date = date if date else event.date
                current_time = start_time if start_time else event.start_time
                update_data["event_datetime"] = datetime.strptime(
                    f"{current_date} {current_time}", "%Y-%m-%d %H:%M"
                )

            if title is not None:
                update_data["title"] = title
            if duration is not None:
                update_data["duration"] = duration
            if description is not None:
                update_data["description"] = description

            await event.set(update_data)
            return event
        except Exception:
            return None

    async def delete_event(self, user_id: str, event_id: str) -> bool:
        """Delete an event."""
        try:
            event = await CalendarEvent.get(PydanticObjectId(event_id))
            if event and event.user_id == user_id:
                await event.delete()
                return True
            return False
        except Exception:
            return False

    async def get_events_on_date(self, user_id: str, date: str) -> List[CalendarEvent]:
        """Get all events for a specific date."""
        return await self.get_events_by_date_range(user_id, date, date)

    async def find_available_slots(
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
        events = await self.get_events_on_date(user_id, date)

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

    async def is_time_available(
        self, user_id: str, date: str, start_time: str, duration: int
    ) -> bool:
        """Check if a specific time slot is available."""
        events = await self.get_events_on_date(user_id, date)

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

    async def create_reminder(
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
        # Parse string to datetime object
        reminder_dt = datetime.fromisoformat(reminder_datetime)

        reminder = Reminder(
            user_id=user_id,
            title=title,
            reminder_datetime=reminder_dt,
            event_id=event_id,
            priority=priority,
            recurrence=recurrence,
            notes=notes,
        )
        await reminder.insert()
        return reminder

    async def create_reminder_for_event(
        self,
        user_id: str,
        event_id: str,
        minutes_before: int,
        title: Optional[str] = None,
        priority: str = "normal",
    ) -> Optional[Reminder]:
        """Create a reminder X minutes before an event."""
        # Get the event
        event = await self.get_event(user_id, event_id)
        if not event:
            return None

        # Calculate reminder time using the event_datetime
        reminder_datetime = event.event_datetime - timedelta(minutes=minutes_before)

        # Use event title if no custom title provided
        if not title:
            title = f"Reminder: {event.title}"

        reminder = Reminder(
            user_id=user_id,
            title=title,
            reminder_datetime=reminder_datetime,
            event_id=event_id,
            minutes_before_event=minutes_before,
            priority=priority,
            notes=f"Reminder for event: {event.title}",
        )
        await reminder.insert()
        return reminder

    async def get_upcoming_reminders(
        self, user_id: str, hours_ahead: int = 24
    ) -> List[Reminder]:
        """Get upcoming reminders within the next X hours."""
        now = datetime.utcnow()
        future = now + timedelta(hours=hours_ahead)

        reminders = (
            await Reminder.find(
                Reminder.user_id == user_id,
                Reminder.status == "pending",
                Reminder.reminder_datetime >= now,
                Reminder.reminder_datetime <= future,
            )
            .sort("reminder_datetime")
            .to_list()
        )

        return reminders

    async def get_pending_reminders(self, user_id: str) -> List[Reminder]:
        """Get all pending reminders for a user."""
        reminders = (
            await Reminder.find(
                Reminder.user_id == user_id,
                Reminder.status == "pending",
            )
            .sort("reminder_datetime")
            .to_list()
        )

        return reminders

    async def mark_reminder_completed(self, user_id: str, reminder_id: str) -> bool:
        """Mark a reminder as completed."""
        try:
            reminder = await Reminder.get(PydanticObjectId(reminder_id))
            if reminder and reminder.user_id == user_id:
                await reminder.set(
                    {"status": "completed", "updated_at": datetime.utcnow()}
                )
                return True
            return False
        except Exception:
            return False

    async def snooze_reminder(
        self, user_id: str, reminder_id: str, snooze_minutes: int
    ) -> Optional[Reminder]:
        """Snooze a reminder by X minutes."""
        try:
            reminder = await Reminder.get(PydanticObjectId(reminder_id))
            if not reminder or reminder.user_id != user_id:
                return None

            new_time = reminder.reminder_datetime + timedelta(minutes=snooze_minutes)

            await reminder.set(
                {
                    "reminder_datetime": new_time,
                    "status": "snoozed",
                    "updated_at": datetime.utcnow(),
                }
            )
            return reminder
        except Exception:
            return None

    async def delete_reminder(self, user_id: str, reminder_id: str) -> bool:
        """Delete a reminder."""
        try:
            reminder = await Reminder.get(PydanticObjectId(reminder_id))
            if reminder and reminder.user_id == user_id:
                await reminder.delete()
                return True
            return False
        except Exception:
            return False


# Global instance
calendar_service = MongoCalendarService()
