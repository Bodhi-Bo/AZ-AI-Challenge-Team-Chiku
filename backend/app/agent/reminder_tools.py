"""
Reminder management tools for creating and managing reminders.
"""

from langchain_core.tools import tool
import logging
from typing import Optional
from app.services.mongo_calendar_service import calendar_service
from app.agent.tool_context import get_current_user_id

# Configure logging
logger = logging.getLogger(__name__)


@tool
async def create_reminder(
    title: str,
    reminder_datetime: str,
    priority: str = "normal",
    recurrence: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """
    Create a standalone reminder (not linked to any event).

    Args:
        title: Reminder title
        reminder_datetime: When to remind in ISO format (YYYY-MM-DDTHH:MM:SS)
        priority: Priority level (low, normal, high) - default normal
        recurrence: Recurrence pattern (once, daily, weekly, monthly) - optional
        notes: Additional notes - optional

    Returns:
        dict: Created reminder details
    """
    user_id = get_current_user_id()
    logger.info("=" * 60)
    logger.info("TOOL: create_reminder")
    logger.info(
        f"Parameters: user_id={user_id}, title={title}, datetime={reminder_datetime}"
    )

    reminder = await calendar_service.create_reminder(
        user_id=user_id,
        title=title,
        reminder_datetime=reminder_datetime,
        priority=priority,
        recurrence=recurrence,
        notes=notes,
    )

    result = {
        "success": True,
        "reminder_id": str(reminder.id),
        "title": reminder.title,
        "reminder_datetime": reminder.reminder_datetime,
        "priority": reminder.priority,
        "status": reminder.status,
    }

    logger.info(f"✓ Reminder created: {reminder.title} at {reminder.reminder_datetime}")
    return result


@tool
async def create_reminder_for_event(
    event_id: str,
    minutes_before: int,
    title: Optional[str] = None,
    priority: str = "normal",
) -> dict:
    """
    Create a reminder X minutes before a calendar event.

    **IMPORTANT**: The event_id parameter must be an ObjectId string obtained from a previous
    query (e.g., get_todays_schedule, get_events_on_date, or find_event_by_title).
    DO NOT use event titles or made-up identifiers as event_id.

    Args:
        event_id: The MongoDB ObjectId string (obtained from a previous query, NOT a title)
        minutes_before: How many minutes before event to remind
        title: Custom reminder title (optional, defaults to "Reminder: {event_title}")
        priority: Priority level (low, normal, high) - default normal

    Returns:
        dict: Created reminder details
    """
    user_id = get_current_user_id()
    logger.info("=" * 60)
    logger.info("TOOL: create_reminder_for_event")
    logger.info(f"Parameters: event_id={event_id}, minutes_before={minutes_before}")

    reminder = await calendar_service.create_reminder_for_event(
        user_id=user_id,
        event_id=event_id,
        minutes_before=minutes_before,
        title=title,
        priority=priority,
    )

    if not reminder:
        logger.warning(f"✗ Event not found: {event_id}")
        return {"success": False, "error": f"Event {event_id} not found"}

    result = {
        "success": True,
        "reminder_id": str(reminder.id),
        "title": reminder.title,
        "reminder_datetime": reminder.reminder_datetime,
        "event_id": str(reminder.event_id),
        "minutes_before_event": reminder.minutes_before_event,
        "priority": reminder.priority,
    }

    logger.info(f"✓ Event reminder created: {minutes_before} min before event")
    return result


@tool
async def get_upcoming_reminders(hours_ahead: int = 24) -> dict:
    """
    Get upcoming reminders within the next X hours.

    Args:
        hours_ahead: How many hours ahead to look (default 24)

    Returns:
        dict: List of upcoming reminders
    """
    user_id = get_current_user_id()
    logger.info("=" * 60)
    logger.info("TOOL: get_upcoming_reminders")
    logger.info(f"Parameters: user_id={user_id}, hours_ahead={hours_ahead}")

    reminders = await calendar_service.get_upcoming_reminders(user_id, hours_ahead)

    reminders_list = [
        {
            "reminder_id": str(reminder.id),
            "title": reminder.title,
            "reminder_datetime": reminder.reminder_datetime,
            "priority": reminder.priority,
            "status": reminder.status,
            "event_id": str(reminder.event_id) if reminder.event_id else None,
        }
        for reminder in reminders
    ]

    result = {
        "success": True,
        "hours_ahead": hours_ahead,
        "count": len(reminders_list),
        "reminders": reminders_list,
    }

    logger.info(f"✓ Found {len(reminders_list)} upcoming reminder(s)")
    return result


@tool
async def get_pending_reminders() -> dict:
    """
    Get all pending (not completed/dismissed) reminders.

    Returns:
        dict: List of pending reminders
    """
    user_id = get_current_user_id()
    logger.info("=" * 60)
    logger.info("TOOL: get_pending_reminders")
    logger.info(f"Parameters: user_id={user_id}")

    reminders = await calendar_service.get_pending_reminders(user_id)

    reminders_list = [
        {
            "reminder_id": str(reminder.id),
            "title": reminder.title,
            "reminder_datetime": reminder.reminder_datetime,
            "priority": reminder.priority,
            "status": reminder.status,
            "event_id": str(reminder.event_id) if reminder.event_id else None,
        }
        for reminder in reminders
    ]

    result = {
        "success": True,
        "count": len(reminders_list),
        "reminders": reminders_list,
    }

    logger.info(f"✓ Found {len(reminders_list)} pending reminder(s)")
    return result


@tool
async def mark_reminder_completed(reminder_id: str) -> dict:
    """
    Mark a reminder as completed.

    Args:
        reminder_id: The reminder ID to mark completed

    Returns:
        dict: Success status
    """
    user_id = get_current_user_id()
    logger.info("=" * 60)
    logger.info("TOOL: mark_reminder_completed")
    logger.info(f"Parameters: user_id={user_id}, reminder_id={reminder_id}")

    success = await calendar_service.mark_reminder_completed(user_id, reminder_id)

    if not success:
        logger.warning(f"✗ Reminder not found: {reminder_id}")
        return {"success": False, "error": f"Reminder {reminder_id} not found"}

    result = {"success": True, "reminder_id": reminder_id, "status": "completed"}

    logger.info(f"✓ Reminder marked completed: {reminder_id}")
    return result


@tool
async def snooze_reminder(reminder_id: str, snooze_minutes: int) -> dict:
    """
    Snooze a reminder by X minutes (delays the reminder time).

    Args:
        reminder_id: The reminder ID to snooze
        snooze_minutes: How many minutes to snooze for

    Returns:
        dict: Updated reminder details
    """
    user_id = get_current_user_id()
    logger.info("=" * 60)
    logger.info("TOOL: snooze_reminder")
    logger.info(
        f"Parameters: user_id={user_id}, reminder_id={reminder_id}, snooze={snooze_minutes}min"
    )

    reminder = await calendar_service.snooze_reminder(
        user_id, reminder_id, snooze_minutes
    )

    if not reminder:
        logger.warning(f"✗ Reminder not found: {reminder_id}")
        return {"success": False, "error": f"Reminder {reminder_id} not found"}

    result = {
        "success": True,
        "reminder_id": str(reminder.id),
        "title": reminder.title,
        "new_reminder_datetime": reminder.reminder_datetime,
        "snoozed_by_minutes": snooze_minutes,
    }

    logger.info(f"✓ Reminder snoozed by {snooze_minutes} minutes")
    return result


@tool
async def delete_reminder(reminder_id: str) -> dict:
    """
    Delete a reminder.

    Args:
        reminder_id: The reminder ID to delete

    Returns:
        dict: Success status
    """
    user_id = get_current_user_id()
    logger.info("=" * 60)
    logger.info("TOOL: delete_reminder")
    logger.info(f"Parameters: user_id={user_id}, reminder_id={reminder_id}")

    success = await calendar_service.delete_reminder(user_id, reminder_id)

    if not success:
        logger.warning(f"✗ Reminder not found: {reminder_id}")
        return {"success": False, "error": f"Reminder {reminder_id} not found"}

    result = {
        "success": True,
        "reminder_id": reminder_id,
        "message": "Reminder deleted",
    }

    logger.info(f"✓ Reminder deleted: {reminder_id}")
    return result
