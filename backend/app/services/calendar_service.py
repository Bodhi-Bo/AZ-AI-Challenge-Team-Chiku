from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel


class CalendarEvent(BaseModel):
    """Represents a calendar event."""

    id: str
    user_id: str
    title: str
    date: str  # YYYY-MM-DD
    start_time: str  # HH:MM
    duration: int  # minutes
    created_at: datetime


class CalendarService:
    """In-memory calendar service for storing and retrieving events."""

    def __init__(self):
        self._events: Dict[str, List[CalendarEvent]] = {}
        self._event_counter = 0

    def create_event(
        self, user_id: str, title: str, date: str, start_time: str, duration: int
    ) -> CalendarEvent:
        """Create a new calendar event."""
        self._event_counter += 1
        event = CalendarEvent(
            id=f"evt_{self._event_counter}",
            user_id=user_id,
            title=title,
            date=date,
            start_time=start_time,
            duration=duration,
            created_at=datetime.now(),
        )

        if user_id not in self._events:
            self._events[user_id] = []

        self._events[user_id].append(event)
        return event

    def get_user_events(self, user_id: str) -> List[CalendarEvent]:
        """Get all events for a user."""
        return self._events.get(user_id, [])

    def get_events_by_date_range(
        self, user_id: str, start_date: str, end_date: Optional[str] = None
    ) -> List[CalendarEvent]:
        """Get events for a user within a date range."""
        user_events = self._events.get(user_id, [])

        if not end_date:
            end_date = start_date

        filtered_events = [
            event for event in user_events if start_date <= event.date <= end_date
        ]
        return sorted(filtered_events, key=lambda e: (e.date, e.start_time))

    def get_event(self, user_id: str, event_id: str) -> Optional[CalendarEvent]:
        """Get a specific event."""
        user_events = self._events.get(user_id, [])
        for event in user_events:
            if event.id == event_id:
                return event
        return None

    def update_event(
        self,
        user_id: str,
        event_id: str,
        title: Optional[str] = None,
        date: Optional[str] = None,
        start_time: Optional[str] = None,
        duration: Optional[int] = None,
    ) -> Optional[CalendarEvent]:
        """Update an existing event."""
        event = self.get_event(user_id, event_id)
        if not event:
            return None

        if title is not None:
            event.title = title
        if date is not None:
            event.date = date
        if start_time is not None:
            event.start_time = start_time
        if duration is not None:
            event.duration = duration

        return event

    def delete_event(self, user_id: str, event_id: str) -> bool:
        """Delete an event."""
        user_events = self._events.get(user_id, [])
        for i, event in enumerate(user_events):
            if event.id == event_id:
                user_events.pop(i)
                return True
        return False


# Global instance
calendar_service = CalendarService()
