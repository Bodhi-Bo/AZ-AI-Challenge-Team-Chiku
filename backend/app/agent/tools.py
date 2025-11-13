"""
Core agent tools including state management.
"""

from langchain_core.tools import tool
import logging
from typing import Optional, Dict, Any
from app.services.calendar_service import calendar_service
from app.services.conversation_service import conversation_service

# Configure logging
logger = logging.getLogger(__name__)


@tool
async def update_user_profile(
    user_id: str, profile_updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update the persistent user profile with learnings from the conversation.

    Call this tool when you've learned something valuable about the user that should
    be remembered across conversations. This is especially important before sending
    a declarative message that ends the conversation.

    **What to track in user_profile:**
    - preferences: Scheduling preferences, communication style, activity preferences
    - patterns: When they're most productive, sleep schedule, exercise routines
    - routines: Regular activities, daily/weekly patterns
    - constraints: Recurring commitments, time blocks
    - emotional_triggers: What stresses them, what helps them focus
    - productivity_windows: Best times for focused work, meetings, breaks
    - wellbeing: Exercise habits, self-care routines, dietary preferences
    - social: Social preferences, interaction patterns

    This profile persists across conversations and helps you provide better support.

    Args:
        user_id: The user's ID
        profile_updates: Dictionary of profile fields to update (merges with existing profile)

    Returns:
        dict: Confirmation of profile update
    """
    logger.info("=" * 60)
    logger.info("TOOL: update_user_profile")
    logger.info(f"User ID: {user_id}")
    logger.info(f"Profile updates: {profile_updates}")

    # Get current state
    current_state = conversation_service.get_conversation_state(user_id)
    current_profile = current_state.user_profile.copy()

    # Deep merge the updates
    updated_profile = conversation_service._deep_merge(current_profile, profile_updates)

    # Update the profile
    conversation_service.update_conversation_state(
        user_id, {"user_profile": updated_profile}
    )

    logger.info(f"✓ User profile updated")
    logger.info(f"  Profile now contains: {list(updated_profile.keys())}")

    return {
        "success": True,
        "message": "User profile updated successfully",
        "profile_keys": list(updated_profile.keys()),
    }


@tool
async def update_working_state(
    user_id: str, state_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update your internal working state based on conversation history and tool results.

    **CRITICAL: This MUST be the first tool you call in every iteration.**

    Synthesize insights from:
    - {{last_state_json}}: Your previous state
    - {{last_tool_actions_and_result}}: Results from your last tool calls
    - Current user message and context

    State Schema:
    Required fields:
    - intent: {high_level_goal, current_objective, priority}
    - reasoning: (string) Your thought process for this iteration

    Recommended optional fields:
    - context: {emotional_state, time_horizon, constraints, preferences}
    - planning: {missing_info, next_microstep, anticipated_user_response}
    - commitments: [{type, id, status, summary}, ...]
    - confidence: 0.0-1.0

    You can add ANY custom fields that help you track state effectively.
    Examples: emotional_trajectory, conversation_phase, user_patterns, etc.

    Args:
        user_id: The user's ID
        state_dict: Your updated working state with insights from last iteration

    Returns:
        dict: Confirmation of state update
    """
    logger.info("=" * 60)
    logger.info("TOOL: update_working_state")
    logger.info(f"User ID: {user_id}")
    logger.info(f"State update: {state_dict}")

    # Validate required fields
    if "intent" not in state_dict:
        logger.warning("Missing required field: intent")
        return {
            "success": False,
            "error": "Missing required field: intent",
        }

    if "reasoning" not in state_dict:
        logger.warning("Missing required field: reasoning")
        return {
            "success": False,
            "error": "Missing required field: reasoning",
        }

    # Actually persist the state update to conversation service
    conversation_service.update_conversation_state(user_id, state_dict)

    logger.info(f"✓ State persisted to conversation service")
    logger.info(
        f"  Intent: {state_dict.get('intent', {}).get('current_objective', 'N/A')}"
    )
    logger.info(f"  Reasoning: {state_dict.get('reasoning', 'N/A')[:100]}...")

    return {
        "success": True,
        "message": "State updated and persisted successfully",
    }


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
