"""
Calendar Event Beanie Document Model
"""

from datetime import datetime, timedelta, timezone
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
    title_embedding: Optional[list[float]] = (
        None  # Vector embedding for semantic search
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @computed_field
    @property
    def date(self) -> str:
        """Return local (MST, UTC-7) date in YYYY-MM-DD format.

        Events are stored in UTC in `event_datetime`. For user-facing fields
        like `date` and `start_time`, we convert to Mountain Standard Time
        so the calendar UI, which operates in MST, shows the expected
        wall-clock day and time.
        """

        mst_offset = timezone(timedelta(hours=-7))
        mst_dt = self.event_datetime.astimezone(mst_offset)
        return mst_dt.strftime("%Y-%m-%d")

    @computed_field
    @property
    def start_time(self) -> str:
        """Return local (MST, UTC-7) time in HH:MM format."""

        mst_offset = timezone(timedelta(hours=-7))
        mst_dt = self.event_datetime.astimezone(mst_offset)
        return mst_dt.strftime("%H:%M")

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
