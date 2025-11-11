from langchain_core.tools import tool
import logging
from typing import Optional
from app.services.calendar_service import calendar_service

# Configure logging
logger = logging.getLogger(__name__)


@tool
def get_events(user_id: str, start_date: str, end_date: Optional[str] = None) -> dict:
    """
    Get calendar events for a user within a date range.

    Args:
        user_id: The user's ID
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (optional, defaults to start_date)

    Returns:
        dict: List of events with their details
    """
    logger.info("=" * 60)
    logger.info("TOOL: get_events")
    logger.info(f"Parameters:")
    logger.info(f"  - user_id: {user_id}")
    logger.info(f"  - start_date: {start_date}")
    logger.info(f"  - end_date: {end_date}")

    events = calendar_service.get_events_by_date_range(user_id, start_date, end_date)

    events_list = [
        {
            "event_id": event.id,
            "title": event.title,
            "date": event.date,
            "start_time": event.start_time,
            "duration": event.duration,
        }
        for event in events
    ]

    result = {
        "success": True,
        "count": len(events_list),
        "events": events_list,
    }

    logger.info(f"✓ Found {len(events_list)} event(s)")
    return result


@tool
def create_calendar_event(
    user_id: str, title: str, date: str, start_time: str, duration: int
) -> dict:
    """
    Create a calendar event.

    Args:
        user_id: The user's ID
        title: Event title
        date: Event date in YYYY-MM-DD format
        start_time: Event start time in HH:MM format
        duration: Event duration in minutes

    Returns:
        dict: Created event details
    """
    logger.info("=" * 60)
    logger.info("TOOL: create_calendar_event")
    logger.info(f"Parameters:")
    logger.info(f"  - user_id: {user_id}")
    logger.info(f"  - title: {title}")
    logger.info(f"  - date: {date}")
    logger.info(f"  - start_time: {start_time}")
    logger.info(f"  - duration: {duration}")

    event = calendar_service.create_event(
        user_id=user_id,
        title=title,
        date=date,
        start_time=start_time,
        duration=duration,
    )

    result = {
        "success": True,
        "event_id": event.id,
        "title": event.title,
        "date": event.date,
        "start_time": event.start_time,
        "duration": event.duration,
    }

    logger.info(f"✓ Event created: {result}")
    return result


@tool
def update_calendar_event(
    user_id: str,
    event_id: str,
    title: Optional[str] = None,
    date: Optional[str] = None,
    start_time: Optional[str] = None,
    duration: Optional[int] = None,
) -> dict:
    """
    Update an existing calendar event.

    Args:
        user_id: The user's ID
        event_id: The event ID to update
        title: New event title (optional)
        date: New event date in YYYY-MM-DD format (optional)
        start_time: New event start time in HH:MM format (optional)
        duration: New event duration in minutes (optional)

    Returns:
        dict: Updated event details or error
    """
    logger.info("=" * 60)
    logger.info("TOOL: update_calendar_event")
    logger.info(f"Parameters:")
    logger.info(f"  - user_id: {user_id}")
    logger.info(f"  - event_id: {event_id}")
    logger.info(f"  - title: {title}")
    logger.info(f"  - date: {date}")
    logger.info(f"  - start_time: {start_time}")
    logger.info(f"  - duration: {duration}")

    event = calendar_service.update_event(
        user_id=user_id,
        event_id=event_id,
        title=title,
        date=date,
        start_time=start_time,
        duration=duration,
    )

    if not event:
        logger.warning(f"✗ Event not found: {event_id}")
        return {"success": False, "error": f"Event {event_id} not found"}

    result = {
        "success": True,
        "event_id": event.id,
        "title": event.title,
        "date": event.date,
        "start_time": event.start_time,
        "duration": event.duration,
    }

    logger.info(f"✓ Event updated: {result}")
    return result


@tool
def delete_calendar_event(user_id: str, event_id: str) -> dict:
    """
    Delete a calendar event.

    Args:
        user_id: The user's ID
        event_id: The event ID to delete

    Returns:
        dict: Success status
    """
    logger.info("=" * 60)
    logger.info("TOOL: delete_calendar_event")
    logger.info(f"Parameters:")
    logger.info(f"  - user_id: {user_id}")
    logger.info(f"  - event_id: {event_id}")

    success = calendar_service.delete_event(user_id, event_id)

    if not success:
        logger.warning(f"✗ Event not found: {event_id}")
        return {"success": False, "error": f"Event {event_id} not found"}

    result = {"success": True, "event_id": event_id, "message": "Event deleted"}

    logger.info(f"✓ Event deleted: {event_id}")
    return result
