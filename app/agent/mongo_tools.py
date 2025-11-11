from langchain_core.tools import tool
import logging
from typing import Optional, List
from app.services.mongo_calendar_service import calendar_service
from datetime import datetime, timedelta

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
    logger.info(
        f"Parameters: user_id={user_id}, start_date={start_date}, end_date={end_date}"
    )

    events = calendar_service.get_events_by_date_range(user_id, start_date, end_date)

    events_list = [
        {
            "event_id": event.id,
            "title": event.title,
            "date": event.date,
            "start_time": event.start_time,
            "duration": event.duration,
            "description": event.description,
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
def get_events_on_date(user_id: str, date: str) -> dict:
    """
    Get all events for a specific date.

    Args:
        user_id: The user's ID
        date: Date in YYYY-MM-DD format

    Returns:
        dict: List of events for that date
    """
    logger.info("=" * 60)
    logger.info("TOOL: get_events_on_date")
    logger.info(f"Parameters: user_id={user_id}, date={date}")

    events = calendar_service.get_events_on_date(user_id, date)

    events_list = [
        {
            "event_id": event.id,
            "title": event.title,
            "date": event.date,
            "start_time": event.start_time,
            "duration": event.duration,
            "description": event.description,
        }
        for event in events
    ]

    result = {
        "success": True,
        "date": date,
        "count": len(events_list),
        "events": events_list,
    }

    logger.info(f"✓ Found {len(events_list)} event(s) on {date}")
    return result


@tool
def find_available_slots(
    user_id: str,
    date: str,
    duration_minutes: int,
    work_start_hour: int = 9,
    work_end_hour: int = 17,
) -> dict:
    """
    Find available time slots on a given date that can fit an event of specified duration.

    Args:
        user_id: The user's ID
        date: Date to check in YYYY-MM-DD format
        duration_minutes: Required duration in minutes
        work_start_hour: Start of work day (default 9am)
        work_end_hour: End of work day (default 5pm)

    Returns:
        dict: List of available time slots
    """
    logger.info("=" * 60)
    logger.info("TOOL: find_available_slots")
    logger.info(
        f"Parameters: user_id={user_id}, date={date}, duration={duration_minutes}min"
    )

    slots = calendar_service.find_available_slots(
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
def check_time_availability(
    user_id: str, date: str, start_time: str, duration: int
) -> dict:
    """
    Check if a specific time slot is available (no conflicts).

    Args:
        user_id: The user's ID
        date: Date in YYYY-MM-DD format
        start_time: Start time in HH:MM format
        duration: Duration in minutes

    Returns:
        dict: Whether the time is available
    """
    logger.info("=" * 60)
    logger.info("TOOL: check_time_availability")
    logger.info(
        f"Parameters: user_id={user_id}, date={date}, time={start_time}, duration={duration}min"
    )

    is_available = calendar_service.is_time_available(
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


@tool
def create_calendar_event(
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

    event = calendar_service.create_event(
        user_id=user_id,
        title=title,
        date=date,
        start_time=start_time,
        duration=duration,
        description=description,
    )

    result = {
        "success": True,
        "event_id": event.id,
        "title": event.title,
        "date": event.date,
        "start_time": event.start_time,
        "duration": event.duration,
        "description": event.description,
    }

    logger.info(f"✓ Event created: {event.title} on {event.date} at {event.start_time}")
    return result


@tool
def update_calendar_event(
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

    Args:
        user_id: The user's ID
        event_id: The event ID to update
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

    event = calendar_service.update_event(
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
        "event_id": event.id,
        "title": event.title,
        "date": event.date,
        "start_time": event.start_time,
        "duration": event.duration,
        "description": event.description,
    }

    logger.info(f"✓ Event updated: {event.title}")
    return result


@tool
def move_event_to_date(
    user_id: str, event_id: str, new_date: str, new_start_time: Optional[str] = None
) -> dict:
    """
    Move an event to a different date, optionally changing the time.
    This is a semantic wrapper around update_calendar_event for moving events.

    Args:
        user_id: The user's ID
        event_id: The event ID to move
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

    event = calendar_service.update_event(
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
        "event_id": event.id,
        "title": event.title,
        "old_date": "moved",
        "new_date": event.date,
        "start_time": event.start_time,
        "duration": event.duration,
    }

    logger.info(f"✓ Event moved: {event.title} → {event.date} at {event.start_time}")
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
    logger.info(f"Parameters: user_id={user_id}, event_id={event_id}")

    success = calendar_service.delete_event(user_id, event_id)

    if not success:
        logger.warning(f"✗ Event not found: {event_id}")
        return {"success": False, "error": f"Event {event_id} not found"}

    result = {"success": True, "event_id": event_id, "message": "Event deleted"}

    logger.info(f"✓ Event deleted: {event_id}")
    return result


@tool
def get_todays_schedule(user_id: str) -> dict:
    """
    Get today's schedule for the user.

    Args:
        user_id: The user's ID

    Returns:
        dict: Today's events
    """
    today = datetime.now().strftime("%Y-%m-%d")
    logger.info("=" * 60)
    logger.info("TOOL: get_todays_schedule")
    logger.info(f"Parameters: user_id={user_id}, today={today}")

    return get_events_on_date.invoke({"user_id": user_id, "date": today})


@tool
def get_tomorrows_schedule(user_id: str) -> dict:
    """
    Get tomorrow's schedule for the user.

    Args:
        user_id: The user's ID

    Returns:
        dict: Tomorrow's events
    """
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    logger.info("=" * 60)
    logger.info("TOOL: get_tomorrows_schedule")
    logger.info(f"Parameters: user_id={user_id}, tomorrow={tomorrow}")

    return get_events_on_date.invoke({"user_id": user_id, "date": tomorrow})


@tool
def get_week_schedule(user_id: str) -> dict:
    """
    Get this week's schedule (next 7 days).

    Args:
        user_id: The user's ID

    Returns:
        dict: This week's events
    """
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    logger.info("=" * 60)
    logger.info("TOOL: get_week_schedule")
    logger.info(f"Parameters: user_id={user_id}, range={start_date} to {end_date}")

    return get_events.invoke(
        {"user_id": user_id, "start_date": start_date, "end_date": end_date}
    )


# ================== REMINDER TOOLS ==================


@tool
def create_reminder(
    user_id: str,
    title: str,
    reminder_datetime: str,
    priority: str = "normal",
    recurrence: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """
    Create a standalone reminder (not linked to any event).

    Args:
        user_id: The user's ID
        title: Reminder title
        reminder_datetime: When to remind in ISO format (YYYY-MM-DDTHH:MM:SS)
        priority: Priority level (low, normal, high) - default normal
        recurrence: Recurrence pattern (once, daily, weekly, monthly) - optional
        notes: Additional notes - optional

    Returns:
        dict: Created reminder details
    """
    logger.info("=" * 60)
    logger.info("TOOL: create_reminder")
    logger.info(
        f"Parameters: user_id={user_id}, title={title}, datetime={reminder_datetime}"
    )

    reminder = calendar_service.create_reminder(
        user_id=user_id,
        title=title,
        reminder_datetime=reminder_datetime,
        priority=priority,
        recurrence=recurrence,
        notes=notes,
    )

    result = {
        "success": True,
        "reminder_id": reminder.id,
        "title": reminder.title,
        "reminder_datetime": reminder.reminder_datetime,
        "priority": reminder.priority,
        "status": reminder.status,
    }

    logger.info(f"✓ Reminder created: {reminder.title} at {reminder.reminder_datetime}")
    return result


@tool
def create_reminder_for_event(
    user_id: str,
    event_id: str,
    minutes_before: int,
    title: Optional[str] = None,
    priority: str = "normal",
) -> dict:
    """
    Create a reminder X minutes before a calendar event.

    Args:
        user_id: The user's ID
        event_id: The event ID to create reminder for
        minutes_before: How many minutes before event to remind
        title: Custom reminder title (optional, defaults to "Reminder: {event_title}")
        priority: Priority level (low, normal, high) - default normal

    Returns:
        dict: Created reminder details
    """
    logger.info("=" * 60)
    logger.info("TOOL: create_reminder_for_event")
    logger.info(f"Parameters: event_id={event_id}, minutes_before={minutes_before}")

    reminder = calendar_service.create_reminder_for_event(
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
        "reminder_id": reminder.id,
        "title": reminder.title,
        "reminder_datetime": reminder.reminder_datetime,
        "event_id": reminder.event_id,
        "minutes_before_event": reminder.minutes_before_event,
        "priority": reminder.priority,
    }

    logger.info(f"✓ Event reminder created: {minutes_before} min before event")
    return result


@tool
def get_upcoming_reminders(user_id: str, hours_ahead: int = 24) -> dict:
    """
    Get upcoming reminders within the next X hours.

    Args:
        user_id: The user's ID
        hours_ahead: How many hours ahead to look (default 24)

    Returns:
        dict: List of upcoming reminders
    """
    logger.info("=" * 60)
    logger.info("TOOL: get_upcoming_reminders")
    logger.info(f"Parameters: user_id={user_id}, hours_ahead={hours_ahead}")

    reminders = calendar_service.get_upcoming_reminders(user_id, hours_ahead)

    reminders_list = [
        {
            "reminder_id": reminder.id,
            "title": reminder.title,
            "reminder_datetime": reminder.reminder_datetime,
            "event_id": reminder.event_id,
            "priority": reminder.priority,
            "status": reminder.status,
        }
        for reminder in reminders
    ]

    result = {
        "success": True,
        "count": len(reminders_list),
        "reminders": reminders_list,
    }

    logger.info(f"✓ Found {len(reminders_list)} upcoming reminder(s)")
    return result


@tool
def get_pending_reminders(user_id: str) -> dict:
    """
    Get all pending reminders for the user.

    Args:
        user_id: The user's ID

    Returns:
        dict: List of pending reminders
    """
    logger.info("=" * 60)
    logger.info("TOOL: get_pending_reminders")
    logger.info(f"Parameters: user_id={user_id}")

    reminders = calendar_service.get_pending_reminders(user_id)

    reminders_list = [
        {
            "reminder_id": reminder.id,
            "title": reminder.title,
            "reminder_datetime": reminder.reminder_datetime,
            "event_id": reminder.event_id,
            "priority": reminder.priority,
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
def mark_reminder_completed(user_id: str, reminder_id: str) -> dict:
    """
    Mark a reminder as completed.

    Args:
        user_id: The user's ID
        reminder_id: The reminder ID to complete

    Returns:
        dict: Success status
    """
    logger.info("=" * 60)
    logger.info("TOOL: mark_reminder_completed")
    logger.info(f"Parameters: user_id={user_id}, reminder_id={reminder_id}")

    success = calendar_service.mark_reminder_completed(user_id, reminder_id)

    if not success:
        logger.warning(f"✗ Reminder not found: {reminder_id}")
        return {"success": False, "error": f"Reminder {reminder_id} not found"}

    result = {"success": True, "reminder_id": reminder_id, "status": "completed"}

    logger.info(f"✓ Reminder marked completed: {reminder_id}")
    return result


@tool
def snooze_reminder(user_id: str, reminder_id: str, snooze_minutes: int) -> dict:
    """
    Snooze a reminder by X minutes.

    Args:
        user_id: The user's ID
        reminder_id: The reminder ID to snooze
        snooze_minutes: How many minutes to snooze

    Returns:
        dict: Updated reminder details
    """
    logger.info("=" * 60)
    logger.info("TOOL: snooze_reminder")
    logger.info(f"Parameters: reminder_id={reminder_id}, snooze={snooze_minutes} min")

    reminder = calendar_service.snooze_reminder(user_id, reminder_id, snooze_minutes)

    if not reminder:
        logger.warning(f"✗ Reminder not found: {reminder_id}")
        return {"success": False, "error": f"Reminder {reminder_id} not found"}

    result = {
        "success": True,
        "reminder_id": reminder.id,
        "title": reminder.title,
        "new_reminder_datetime": reminder.reminder_datetime,
        "status": reminder.status,
    }

    logger.info(
        f"✓ Reminder snoozed: {snooze_minutes} min → {reminder.reminder_datetime}"
    )
    return result


@tool
def delete_reminder(user_id: str, reminder_id: str) -> dict:
    """
    Delete a reminder.

    Args:
        user_id: The user's ID
        reminder_id: The reminder ID to delete

    Returns:
        dict: Success status
    """
    logger.info("=" * 60)
    logger.info("TOOL: delete_reminder")
    logger.info(f"Parameters: user_id={user_id}, reminder_id={reminder_id}")

    success = calendar_service.delete_reminder(user_id, reminder_id)

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
