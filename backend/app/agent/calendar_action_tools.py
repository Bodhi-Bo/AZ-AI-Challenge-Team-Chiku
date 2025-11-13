"""
Calendar action tools for creating, updating, and deleting events.
All tools in this file modify calendar data.
"""

from langchain_core.tools import tool
import logging
from typing import Optional
from app.services.mongo_calendar_service import calendar_service

# Configure logging
logger = logging.getLogger(__name__)


@tool
async def create_calendar_event(
    user_id: str,
    title: str,
    date: str,
    start_time: str,
    duration: int,
    description: Optional[str] = None,
) -> dict:
    """
    Create a new calendar event.

    Args:
        user_id: The user's ID
        title: Event title
        date: Event date in YYYY-MM-DD format
        start_time: Event start time in HH:MM format
        duration: Event duration in minutes
        description: Optional event description

    Returns:
        dict: Created event details
    """
    logger.info("=" * 60)
    logger.info("TOOL: create_calendar_event")
    logger.info(
        f"Parameters: user_id={user_id}, title={title}, date={date}, time={start_time}, duration={duration}min"
    )

    event = await calendar_service.create_event(
        user_id=user_id,
        title=title,
        date=date,
        start_time=start_time,
        duration=duration,
        description=description,
    )

    result = {
        "success": True,
        "event_id": str(event.id),
        "title": event.title,
        "date": event.date,
        "start_time": event.start_time,
        "duration": event.duration,
        "description": event.description,
    }

    logger.info(f"✓ Event created: {event.title} on {event.date} at {event.start_time}")
    return result


@tool
async def update_calendar_event(
    user_id: str,
    event_id: str,
    title: Optional[str] = None,
    date: Optional[str] = None,
    start_time: Optional[str] = None,
    duration: Optional[int] = None,
    description: Optional[str] = None,
) -> dict:
    """
    Update an existing calendar event. Only provided fields will be updated.

    **IMPORTANT**: The event_id parameter must be an ObjectId string obtained from a previous
    query (e.g., get_todays_schedule, get_events_on_date, or find_event_by_title).
    DO NOT use event titles or made-up identifiers as event_id.

    Workflow:
        1. First call find_event_by_title or get_events_on_date to find the event
        2. Extract the event_id from the results (e.g., "691317c99da9a2b1525f35c9")
        3. Then call this function with that event_id

    Args:
        user_id: The user's ID
        event_id: The MongoDB ObjectId string (obtained from a previous query, NOT a title)
        title: New event title (optional)
        date: New event date in YYYY-MM-DD format (optional)
        start_time: New event start time in HH:MM format (optional)
        duration: New event duration in minutes (optional)
        description: New event description (optional)

    Returns:
        dict: Updated event details or error
    """
    logger.info("=" * 60)
    logger.info("TOOL: update_calendar_event")
    logger.info(f"Parameters: user_id={user_id}, event_id={event_id}")
    logger.info(
        f"  Updates: title={title}, date={date}, time={start_time}, duration={duration}"
    )

    event = await calendar_service.update_event(
        user_id=user_id,
        event_id=event_id,
        title=title,
        date=date,
        start_time=start_time,
        duration=duration,
        description=description,
    )

    if not event:
        logger.warning(f"✗ Event not found: {event_id}")
        return {"success": False, "error": f"Event {event_id} not found"}

    result = {
        "success": True,
        "event_id": str(event.id),
        "title": event.title,
        "date": event.date,
        "start_time": event.start_time,
        "duration": event.duration,
        "description": event.description,
    }

    logger.info(f"✓ Event updated: {event.title}")
    return result


@tool
async def move_event_to_date(
    user_id: str, event_id: str, new_date: str, new_start_time: Optional[str] = None
) -> dict:
    """
    Move an event to a different date, optionally changing the time.
    This is a semantic wrapper around update_calendar_event for moving events.

    **IMPORTANT**: The event_id parameter must be an ObjectId string obtained from a previous
    query (e.g., get_todays_schedule, get_events_on_date, or find_event_by_title).
    DO NOT use event titles or made-up identifiers as event_id.

    Workflow:
        1. First call find_event_by_title or get_events_on_date to find the event
        2. Extract the event_id from the results (e.g., "691317c99da9a2b1525f35c9")
        3. Then call this function with that event_id

    Args:
        user_id: The user's ID
        event_id: The MongoDB ObjectId string (obtained from a previous query, NOT a title)
        new_date: New date in YYYY-MM-DD format
        new_start_time: New start time in HH:MM format (optional, keeps original time if not provided)

    Returns:
        dict: Updated event details
    """
    logger.info("=" * 60)
    logger.info("TOOL: move_event_to_date")
    logger.info(
        f"Parameters: event_id={event_id}, new_date={new_date}, new_time={new_start_time}"
    )

    event = await calendar_service.update_event(
        user_id=user_id,
        event_id=event_id,
        date=new_date,
        start_time=new_start_time if new_start_time else None,
    )

    if not event:
        logger.warning(f"✗ Event not found: {event_id}")
        return {"success": False, "error": f"Event {event_id} not found"}

    result = {
        "success": True,
        "event_id": str(event.id),
        "title": event.title,
        "old_date": "moved",
        "new_date": event.date,
        "start_time": event.start_time,
        "duration": event.duration,
    }

    logger.info(f"✓ Event moved: {event.title} → {event.date} at {event.start_time}")
    return result


@tool
async def delete_calendar_event(user_id: str, event_id: str) -> dict:
    """
    Delete a calendar event.

    **IMPORTANT**: The event_id parameter must be an ObjectId string obtained from a previous
    query (e.g., get_todays_schedule, get_events_on_date, or find_event_by_title).
    DO NOT use event titles or made-up identifiers as event_id.

    Workflow:
        1. First call find_event_by_title or get_events_on_date to find the event
        2. Extract the event_id from the results (e.g., "691317c99da9a2b1525f35c9")
        3. Then call this function with that event_id

    Args:
        user_id: The user's ID
        event_id: The MongoDB ObjectId string (obtained from a previous query, NOT a title)

    Returns:
        dict: Success status
    """
    logger.info("=" * 60)
    logger.info("TOOL: delete_calendar_event")
    logger.info(f"Parameters: user_id={user_id}, event_id={event_id}")

    success = await calendar_service.delete_event(user_id, event_id)

    if not success:
        logger.warning(f"✗ Event not found: {event_id}")
        return {"success": False, "error": f"Event {event_id} not found"}

    result = {"success": True, "event_id": event_id, "message": "Event deleted"}

    logger.info(f"✓ Event deleted: {event_id}")
    return result
