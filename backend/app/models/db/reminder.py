"""
Reminder Beanie Document Model
"""

from datetime import datetime
from typing import Optional
from beanie import Document
from pydantic import Field


class Reminder(Document):
    """Represents a reminder stored in MongoDB via Beanie."""

    user_id: str
    title: str
    reminder_datetime: datetime  # Full datetime object
    event_id: Optional[str] = None  # Link to CalendarEvent if this is event-based
    minutes_before_event: Optional[int] = None  # For event-based reminders
    priority: str = "normal"  # low, normal, high
    status: str = "pending"  # pending, completed, snoozed
    recurrence: Optional[str] = None  # once, daily, weekly, monthly
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "reminders"  # Collection name
        indexes = [
            [("user_id", 1), ("reminder_datetime", 1)],
            [("user_id", 1), ("status", 1)],
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "title": "Prepare presentation",
                "reminder_datetime": "2025-11-15T13:00:00",
                "priority": "high",
                "status": "pending",
                "notes": "Gather slides from last quarter",
            }
        }
