"""
Create a test Tennis event at 5pm MST on Nov 15, 2025
to verify the timezone fix works.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.models.db.calendar_event import CalendarEvent
from app.models.db.reminder import Reminder
from app.config import MONGO_DB_URI
from app.utils.load_env import load_env_vars
from app.services.mongo_calendar_service import calendar_service
from app.agent_tools.mongo_tools import find_event_by_title, get_todays_schedule
from app.agent_tools.tool_context import set_current_user_id, reset_current_user_id

load_env_vars()


async def test_complete_flow():
    """
    Complete test:
    1. Create a Tennis event at 5pm MST on Nov 15, 2025
    2. Query for it using find_event_by_title with date="2025-11-15"
    3. Verify it's found correctly
    """

    # Initialize database
    client = AsyncIOMotorClient(MONGO_DB_URI)
    await init_beanie(
        database=client.calendar_db, document_models=[CalendarEvent, Reminder]
    )

    user_id = "user_123"
    context_token = set_current_user_id(user_id)

    try:
        print("=" * 80)
        print("COMPLETE TIMEZONE FIX TEST")
        print("=" * 80)

        # Step 1: Create Tennis event at 5pm MST on Nov 15
        print("\n1. Creating Tennis event at 5:00 PM MST on 2025-11-15...")
        event = await calendar_service.create_event(
            user_id=user_id,
            title="Tennis",
            date="2025-11-15",
            start_time="17:00",  # 5:00 PM MST
            duration=60,
            description="Tennis session",
        )

        print(f"✅ Created event:")
        print(f"   Title: {event.title}")
        print(f"   Event DateTime (UTC): {event.event_datetime}")
        print(f"   Date property (MST): {event.date}")
        print(f"   Start Time property (MST): {event.start_time}")

        # Step 2: Query using find_event_by_title with date="2025-11-15"
        print("\n2. Querying for Tennis on date='2025-11-15'...")
        result = await find_event_by_title.ainvoke(
            {"title_query": "Tennis", "date": "2025-11-15"}
        )

        print(f"\nQuery result: {result.get('count', 0)} events found")

        # Step 3: Verify
        if result.get("count", 0) > 0:
            print("\n✅ SUCCESS! Tennis event found on 2025-11-15!")
            for evt in result.get("events", []):
                print(f"   - {evt['title']} at {evt['start_time']} on {evt['date']}")
            print("\n🎉 TIMEZONE FIX WORKS CORRECTLY!")
        else:
            print("\n❌ FAILED: Tennis event not found on 2025-11-15")
            print("   This means the timezone fix didn't work as expected.")

        # Also test get_todays_schedule
        print("\n3. Testing get_todays_schedule...")
        today_result = await get_todays_schedule.ainvoke({})
        print(f"   Today's schedule: {today_result.get('count', 0)} events")

        # Cleanup
        print("\n4. Cleaning up test event...")
        await event.delete()
        print("   ✓ Test event deleted")

        print("\n" + "=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)

    finally:
        reset_current_user_id(context_token)


if __name__ == "__main__":
    asyncio.run(test_complete_flow())
