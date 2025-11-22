"""
Debug script to check existing events in the database.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.models.db.calendar_event import CalendarEvent
from app.models.db.reminder import Reminder
from app.config import MONGO_DB_URI
from app.utils.load_env import load_env_vars
from app.agent_tools.mongo_tools import find_event_by_title
from app.agent_tools.tool_context import set_current_user_id, reset_current_user_id

load_env_vars()


async def debug_events():
    """Debug existing events."""

    # Initialize database
    client = AsyncIOMotorClient(MONGO_DB_URI)
    await init_beanie(
        database=client.calendar_assistant, document_models=[CalendarEvent, Reminder]
    )

    user_id = "user_123"
    context_token = set_current_user_id(user_id)

    try:
        print("=" * 80)
        print("DEBUG EXISTING EVENTS")
        print("=" * 80)

        # Get all events directly
        print("\n1. Querying all events for user_123...")
        events = await CalendarEvent.find(CalendarEvent.user_id == user_id).to_list()

        print(f"\nFound {len(events)} events:")
        for event in events:
            print(f"\n  Title: {event.title}")
            print(f"  event_datetime: {event.event_datetime}")
            print(f"  event_datetime type: {type(event.event_datetime)}")
            print(f"  event_datetime.tzinfo: {event.event_datetime.tzinfo}")
            print(f"  Computed date property: {event.date}")
            print(f"  Computed start_time property: {event.start_time}")

        # Now test find_event_by_title with date filter
        print("\n\n2. Testing find_event_by_title for 'Tennis' on 2025-11-15...")
        result = await find_event_by_title.ainvoke(
            {"title_query": "Tennis", "date": "2025-11-15"}
        )

        print(f"\nResult: {result}")

        if result.get("count", 0) > 0:
            print("\n✅ Tennis found on 2025-11-15!")
        else:
            print("\n❌ Tennis NOT found on 2025-11-15")

            # Try without date filter
            print("\n3. Trying without date filter...")
            result_all = await find_event_by_title.ainvoke({"title_query": "Tennis"})
            print(f"\nResult: {result_all}")

    finally:
        reset_current_user_id(context_token)


if __name__ == "__main__":
    asyncio.run(debug_events())
