"""
Test script to verify timezone fix for calendar queries.

This script tests that:
1. Events stored in UTC are correctly found when querying by MST date
2. get_todays_schedule uses MST "today"
3. find_event_by_title can find events on the correct MST date
"""

import asyncio
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.services.mongo_calendar_service import calendar_service
from app.agent_tools.mongo_tools import find_event_by_title, get_todays_schedule
from app.agent_tools.tool_context import set_current_user_id, reset_current_user_id
from app.utils.load_env import load_env_vars
from app.models.db.calendar_event import CalendarEvent
from app.models.db.reminder import Reminder
from app.config import MONGO_DB_URI

# Initialize environment
load_env_vars()


async def init_db():
    """Initialize Beanie with MongoDB."""
    client = AsyncIOMotorClient(MONGO_DB_URI)
    await init_beanie(
        database=client.calendar_db, document_models=[CalendarEvent, Reminder]
    )


async def test_timezone_fix():
    """Test that timezone fix allows finding events on correct MST date."""

    # Initialize database
    await init_db()

    user_id = "user_123"
    context_token = set_current_user_id(user_id)

    try:
        print("=" * 80)
        print("TIMEZONE FIX TEST")
        print("=" * 80)

        # Get the existing Tennis event
        print("\n1. Testing find_event_by_title for 'Tennis' on 2025-11-15...")
        result = await find_event_by_title.ainvoke(
            {"title_query": "Tennis", "date": "2025-11-15"}
        )

        print(f"\nResult: {result}")

        if result.get("count", 0) > 0:
            print("✅ SUCCESS: Tennis event found on 2025-11-15!")
            for event in result.get("events", []):
                print(
                    f"   - {event['title']} at {event['start_time']} on {event['date']}"
                )
        else:
            print("❌ FAILED: Tennis event not found on 2025-11-15")
            print("\nLet's check what date the Tennis event is on...")

            # Search without date filter
            all_tennis = await find_event_by_title.ainvoke({"title_query": "Tennis"})

            print(f"\nAll Tennis events found: {all_tennis.get('count', 0)}")
            for event in all_tennis.get("events", []):
                print(
                    f"   - {event['title']} on {event['date']} at {event['start_time']}"
                )

        # Test get_todays_schedule
        print("\n2. Testing get_todays_schedule (should use MST today)...")
        today_result = await get_todays_schedule.ainvoke({})

        print(f"\nToday's schedule: {today_result.get('count', 0)} events")
        for event in today_result.get("events", []):
            print(f"   - {event['title']} at {event['start_time']}")

        # Calculate what "today" is in MST
        mst_offset = timedelta(hours=-7)
        today_mst = (datetime.now(timezone.utc) + mst_offset).strftime("%Y-%m-%d")
        print(f"\n   MST Today: {today_mst}")

        print("\n" + "=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)

    finally:
        reset_current_user_id(context_token)


if __name__ == "__main__":
    asyncio.run(test_timezone_fix())
