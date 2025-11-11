"""
Calendar Event Beanie Document Model
"""

from datetime import datetime
from typing import Optional
from beanie import Document
from pydantic import Field, computed_field


class CalendarEvent(Document):
    """Represents a calendar event stored in MongoDB via Beanie."""

    user_id: str
    title: str
    event_datetime: datetime  # Full datetime of the event
    duration: int  # minutes
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @computed_field
    @property
    def date(self) -> str:
        """Return date in YYYY-MM-DD format."""
        return self.event_datetime.strftime("%Y-%m-%d")

    @computed_field
    @property
    def start_time(self) -> str:
        """Return time in HH:MM format."""
        return self.event_datetime.strftime("%H:%M")

    class Settings:
        name = "events"  # Collection name
        indexes = [
            [("user_id", 1), ("event_datetime", 1)],
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "title": "Team Meeting",
                "event_datetime": "2025-11-15T14:00:00",
                "duration": 60,
                "description": "Weekly team sync-up",
            }
        }
