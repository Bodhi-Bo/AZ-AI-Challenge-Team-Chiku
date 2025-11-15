"""
Availability checking tools for finding free time slots.
"""

from langchain_core.tools import tool
import logging
from app.services.mongo_calendar_service import calendar_service
from app.agent_tools.tool_context import get_current_user_id

# Configure logging
logger = logging.getLogger(__name__)


@tool
async def find_available_slots(
    date: str,
    duration_minutes: int,
    work_start_hour: int = 9,
    work_end_hour: int = 17,
) -> dict:
    """
    Find available time slots on a given date that can fit an event of specified duration.

    Args:
        date: Date to check in YYYY-MM-DD format
        duration_minutes: Required duration in minutes
        work_start_hour: Start of work day (default 9am)
        work_end_hour: End of work day (default 5pm)

    Returns:
        dict: List of available time slots
    """
    user_id = get_current_user_id()
    logger.info("=" * 60)
    logger.info("TOOL: find_available_slots")
    logger.info(
        f"Parameters: user_id={user_id}, date={date}, duration={duration_minutes}min"
    )

    slots = await calendar_service.find_available_slots(
        user_id, date, duration_minutes, (work_start_hour, work_end_hour)
    )

    result = {
        "success": True,
        "date": date,
        "duration_needed": duration_minutes,
        "available_slots": slots,
        "count": len(slots),
    }

    logger.info(f"✓ Found {len(slots)} available slot(s)")
    return result


@tool
async def check_time_availability(date: str, start_time: str, duration: int) -> dict:
    """
    Check if a specific time slot is available (no conflicts).

    Args:
        date: Date in YYYY-MM-DD format
        start_time: Start time in HH:MM format
        duration: Duration in minutes

    Returns:
        dict: Whether the time is available
    """
    user_id = get_current_user_id()
    logger.info("=" * 60)
    logger.info("TOOL: check_time_availability")
    logger.info(
        f"Parameters: user_id={user_id}, date={date}, time={start_time}, duration={duration}min"
    )

    is_available = await calendar_service.is_time_available(
        user_id, date, start_time, duration
    )

    result = {
        "success": True,
        "date": date,
        "start_time": start_time,
        "duration": duration,
        "is_available": is_available,
    }

    logger.info(f"✓ Time slot is {'available' if is_available else 'NOT available'}")
    return result
