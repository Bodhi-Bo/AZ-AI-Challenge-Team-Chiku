"""
Simple script to check what events exist in the database.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from datetime import datetime, timezone

from app.models.db.calendar_event import CalendarEvent
from app.models.db.reminder import Reminder
from app.config import MONGO_DB_URI
from app.utils.load_env import load_env_vars

load_env_vars()


async def check_events():
    """Check all events in the database."""

    # Initialize database
    client = AsyncIOMotorClient(MONGO_DB_URI)
    await init_beanie(
        database=client.calendar_db, document_models=[CalendarEvent, Reminder]
    )

    print("=" * 80)
    print("DATABASE EVENTS CHECK")
    print("=" * 80)

    # Get all events for user_123
    events = await CalendarEvent.find(CalendarEvent.user_id == "user_123").to_list()

    print(f"\nFound {len(events)} events for user_123:")
    print()

    for event in events:
        print(f"Event: {event.title}")
        print(f"  ID: {event.id}")
        print(f"  Event DateTime (UTC): {event.event_datetime}")
        print(f"  Date property: {event.date}")
        print(f"  Start Time property: {event.start_time}")
        print(f"  Duration: {event.duration} minutes")
        print(f"  Description: {event.description}")
        print()


if __name__ == "__main__":
    asyncio.run(check_events())
