"""
Calendar query tools for reading events and schedules.
All tools in this file are read-only - they don't modify calendar data.
"""

from langchain_core.tools import tool
import logging
from typing import Optional
from datetime import datetime, timedelta
from app.services.mongo_calendar_service import calendar_service
from app.utils.embedding_util import generate_embedding, cosine_similarity

# Configure logging
logger = logging.getLogger(__name__)


@tool
async def get_events(
    user_id: str, start_date: str, end_date: Optional[str] = None
) -> dict:
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

    events = await calendar_service.get_events_by_date_range(
        user_id, start_date, end_date
    )

    events_list = [
        {
            "event_id": str(event.id),
            "title": event.title,
            "date": event.date,
            "start_time": event.start_time,
            "duration": event.duration,
            "description": event.description,
        }
        for event in events
    ]

    result = {"success": True, "count": len(events_list), "events": events_list}

    logger.info(f"✓ Found {len(events_list)} event(s)")
    return result


@tool
async def get_events_on_date(user_id: str, date: str) -> dict:
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

    events = await calendar_service.get_events_on_date(user_id, date)

    events_list = [
        {
            "event_id": str(event.id),
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
async def get_todays_schedule(user_id: str) -> dict:
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

    return await get_events_on_date.ainvoke({"user_id": user_id, "date": today})


@tool
async def get_tomorrows_schedule(user_id: str) -> dict:
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

    return await get_events_on_date.ainvoke({"user_id": user_id, "date": tomorrow})


@tool
async def get_week_schedule(user_id: str) -> dict:
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

    return await get_events.ainvoke(
        {"user_id": user_id, "start_date": start_date, "end_date": end_date}
    )


@tool
async def find_event_by_title(
    user_id: str, title_query: str, date: Optional[str] = None
) -> dict:
    """
    Search for events by title using semantic similarity (vector embeddings).
    Uses cosine similarity with a 0.7 threshold for matching.

    **IMPORTANT**: Use this tool when you need to find the event_id for updating, moving,
    or deleting an event that the user refers to by name/title.

    The event_id returned by this tool must be used as input to update_calendar_event,
    move_event_to_date, or delete_calendar_event.

    Args:
        user_id: The user's ID
        title_query: Title or partial title to search for (semantic search enabled)
        date: Optional date to narrow search (YYYY-MM-DD format). If not provided, searches all dates.

    Returns:
        dict: Matching events with their event_ids, titles, dates, times, and similarity scores

    Example:
        User says "move my yoga session to tomorrow"
        1. Call find_event_by_title(user_id="user_123", title_query="yoga")
        2. Get back event_id "691317c99da9a2b1525f35c9" with similarity score 0.95
        3. Call move_event_to_date(user_id="user_123", event_id="691317c99da9a2b1525f35c9", new_date="2025-11-12")
    """
    logger.info("=" * 60)
    logger.info("TOOL: find_event_by_title (SEMANTIC SEARCH)")
    logger.info(
        f"Parameters: user_id={user_id}, title_query='{title_query}', date={date}"
    )

    # If date is provided, search only that date
    if date:
        events = await calendar_service.get_events_on_date(user_id, date)
    else:
        # Search all events (get a wide range)
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        events = await calendar_service.get_events_by_date_range(
            user_id, start_date, end_date
        )

    # Generate embedding for the search query
    query_embedding = generate_embedding(title_query)

    # Calculate similarity scores for all events
    SIMILARITY_THRESHOLD = 0.7
    matching_events = []

    logger.info(f"Fetched {len(events)} events for user, calculating similarities...")

    for event in events:
        # Skip events without embeddings (legacy events)
        if not event.title_embedding:
            # Fallback to keyword search for legacy events
            if title_query.lower() in event.title.lower():
                matching_events.append((event, 0.5))  # Lower score for keyword match
                logger.info(f"  Legacy keyword match: '{event.title}' (score: 0.5)")
            continue

        # Calculate cosine similarity
        similarity = cosine_similarity(query_embedding, event.title_embedding)

        # Log all events with their similarity scores for debugging
        logger.debug(f"  '{event.title}' similarity: {similarity:.3f}")

        if similarity >= SIMILARITY_THRESHOLD:
            matching_events.append((event, similarity))
            logger.info(
                f"  Match found: '{event.title}' (similarity: {similarity:.3f})"
            )

    # Sort by similarity score (descending)
    matching_events.sort(key=lambda x: x[1], reverse=True)

    # Format results
    events_list = [
        {
            "event_id": str(event.id),
            "title": event.title,
            "date": event.date,
            "start_time": event.start_time,
            "duration": event.duration,
            "description": event.description,
            "similarity_score": round(similarity, 3),  # Include similarity score
        }
        for event, similarity in matching_events
    ]

    result = {
        "success": True,
        "query": title_query,
        "count": len(events_list),
        "events": events_list,
        "note": (
            "Results sorted by semantic similarity. Multiple matches returned for agent to choose from."
            if len(events_list) > 1
            else None
        ),
    }

    if len(events_list) == 0:
        logger.info(
            f"✗ No events found matching '{title_query}' (threshold: {SIMILARITY_THRESHOLD})"
        )
    else:
        logger.info(f"✓ Found {len(events_list)} event(s) matching '{title_query}'")
        for event, similarity in matching_events[:3]:  # Log top 3
            logger.info(f"  - '{event.title}' (similarity: {similarity:.3f})")

    return result
