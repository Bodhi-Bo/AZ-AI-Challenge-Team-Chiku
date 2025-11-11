from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import re
import logging
from datetime import datetime
from dateutil import parser as date_parser
from app.agent.state import AgentState
from app.agent.tools import create_calendar_event
from app.config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    CLASSIFIER_PROMPT,
    INFO_GATHERER_PROMPT,
    EVENT_CREATOR_PROMPT,
    CASUAL_CHAT_PROMPT,
)

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


# Initialize LLM
llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0.7)


def classify_intent(state: AgentState) -> AgentState:
    """Classify the user's intent from their latest message."""
    logger.info("=" * 60)
    logger.info("NODE: classify_intent")

    if not state["messages"]:
        logger.warning("No messages in state, setting intent to unknown")
        state["intent"] = "unknown"
        state["next_action"] = "end"
        return state

    # Check if we're already in a calendar event flow
    # If we have any event info partially collected, continue gathering
    has_partial_event_info = any(
        [
            state.get("event_title"),
            state.get("event_date"),
            state.get("event_start_time"),
            state.get("event_duration"),
        ]
    )

    if has_partial_event_info:
        logger.info(f"Partial event info detected - continuing calendar event flow")
        logger.info(
            f"  Current: title={state.get('event_title')}, date={state.get('event_date')}, "
            f"time={state.get('event_start_time')}, duration={state.get('event_duration')}"
        )
        state["intent"] = "calendar_event"
        state["next_action"] = "gather_info"
        logger.info("✓ Intent: CALENDAR_EVENT (continuing) → Next: gather_info")
        return state

    latest_message = state["messages"][-1]["content"]
    logger.info(f"Latest message: {latest_message}")

    # Use LLM to classify with conversation context
    # Include last few messages for context
    context_messages = (
        state["messages"][-3:] if len(state["messages"]) > 1 else state["messages"]
    )
    context_text = "\n".join(
        [f"{msg.get('role', 'user')}: {msg['content']}" for msg in context_messages]
    )

    prompt = CLASSIFIER_PROMPT.format(user_message=latest_message, context=context_text)
    logger.info("Calling LLM for intent classification...")
    response = llm.invoke([HumanMessage(content=prompt)])

    classification = str(response.content).strip().lower()
    logger.info(f"LLM Classification result: {classification}")

    if "calendar" in classification or "event" in classification:
        state["intent"] = "calendar_event"
        state["next_action"] = "gather_info"
        logger.info("✓ Intent: CALENDAR_EVENT → Next: gather_info")
    else:
        state["intent"] = "casual_chat"
        state["next_action"] = "chat"
        logger.info("✓ Intent: CASUAL_CHAT → Next: chat")

    return state


def gather_event_info(state: AgentState) -> AgentState:
    """
    Gather calendar event information from user.
    Extract info from message or ask for missing details.
    """
    logger.info("=" * 60)
    logger.info("NODE: gather_event_info")

    latest_message = state["messages"][-1]["content"]
    logger.info(f"Processing message: {latest_message}")

    # Try to extract information from the message
    logger.info("Attempting to extract event information...")
    extracted_info = _extract_event_info(latest_message, state)
    logger.info(f"Extracted info: {extracted_info}")

    # Update state with extracted info
    if extracted_info.get("title") and not state.get("event_title"):
        state["event_title"] = extracted_info["title"]
        logger.info(f"✓ Title set: {state['event_title']}")
    if extracted_info.get("date") and not state.get("event_date"):
        state["event_date"] = extracted_info["date"]
        logger.info(f"✓ Date set: {state['event_date']}")
    if extracted_info.get("start_time") and not state.get("event_start_time"):
        state["event_start_time"] = extracted_info["start_time"]
        logger.info(f"✓ Start time set: {state['event_start_time']}")
    if extracted_info.get("duration") and not state.get("event_duration"):
        state["event_duration"] = extracted_info["duration"]
        logger.info(f"✓ Duration set: {state['event_duration']} minutes")

    # Log current state
    logger.info("Current event details:")
    logger.info(f"  - Title: {state.get('event_title', 'Not provided')}")
    logger.info(f"  - Date: {state.get('event_date', 'Not provided')}")
    logger.info(f"  - Start Time: {state.get('event_start_time', 'Not provided')}")
    logger.info(f"  - Duration: {state.get('event_duration', 'Not provided')}")

    # Check if we have all required information
    if all(
        [
            state.get("event_title"),
            state.get("event_date"),
            state.get("event_start_time"),
            state.get("event_duration"),
        ]
    ):
        state["next_action"] = "create_event"
        logger.info("✓ All information collected → Next: create_event")
        return state

    # Ask for missing information using LLM
    logger.info("Missing information, asking LLM to gather more details...")
    prompt = INFO_GATHERER_PROMPT.format(
        title=state.get("event_title", "Not provided"),
        date=state.get("event_date", "Not provided"),
        start_time=state.get("event_start_time", "Not provided"),
        duration=state.get("event_duration", "Not provided"),
        user_message=latest_message,
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    state["response"] = str(response.content).strip()
    state["next_action"] = "gather_info"  # Stay in gathering mode
    logger.info(f"Agent response: {state['response']}")
    logger.info("✓ Next: gather_info (waiting for more input)")

    return state


def create_event(state: AgentState) -> AgentState:
    """Create the calendar event and confirm to user."""
    logger.info("=" * 60)
    logger.info("NODE: create_event")
    logger.info("Creating calendar event with details:")
    logger.info(f"  - User ID: {state['user_id']}")
    logger.info(f"  - Title: {state['event_title']}")
    logger.info(f"  - Date: {state['event_date']}")
    logger.info(f"  - Start Time: {state['event_start_time']}")
    logger.info(f"  - Duration: {state['event_duration']} minutes")

    # Create the event
    logger.info("Calling create_calendar_event tool...")
    result = create_calendar_event.invoke(
        {
            "user_id": state["user_id"],
            "title": state["event_title"],
            "date": state["event_date"],
            "start_time": state["event_start_time"],
            "duration": state["event_duration"],
        }
    )
    logger.info(f"✓ Event created successfully! Event ID: {result.get('event_id')}")

    # Generate confirmation message
    logger.info("Generating confirmation message...")
    prompt = EVENT_CREATOR_PROMPT.format(
        title=state["event_title"],
        date=state["event_date"],
        start_time=state["event_start_time"],
        duration=state["event_duration"],
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    state["response"] = str(response.content).strip()
    logger.info(f"Confirmation message: {state['response']}")

    # Reset event info for next interaction
    logger.info("Resetting event state for next interaction...")
    state["event_title"] = None
    state["event_date"] = None
    state["event_start_time"] = None
    state["event_duration"] = None
    state["intent"] = None
    state["next_action"] = "end"
    logger.info("✓ Next: end")

    return state


def casual_chat(state: AgentState) -> AgentState:
    """Handle casual conversation."""
    logger.info("=" * 60)
    logger.info("NODE: casual_chat")

    latest_message = state["messages"][-1]["content"]
    logger.info(f"User message: {latest_message}")

    logger.info("Generating casual chat response...")
    prompt = CASUAL_CHAT_PROMPT.format(user_message=latest_message)
    response = llm.invoke([HumanMessage(content=prompt)])

    state["response"] = str(response.content).strip()
    state["next_action"] = "end"
    logger.info(f"Agent response: {state['response']}")
    logger.info("✓ Next: end")

    return state


def _extract_event_info(message: str, current_state: AgentState) -> dict:
    """
    Extract event information from user message.
    This is a simple extraction - could be enhanced with better NLP.
    """
    info = {}

    # Try to extract date patterns
    date_patterns = [
        r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
        r"\d{1,2}/\d{1,2}/\d{4}",  # MM/DD/YYYY
        r"(today|tomorrow|next \w+)",  # Relative dates
    ]

    for pattern in date_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            try:
                date_str = match.group(0)
                if date_str.lower() == "today":
                    info["date"] = datetime.now().strftime("%Y-%m-%d")
                elif date_str.lower() == "tomorrow":
                    from datetime import timedelta

                    info["date"] = (datetime.now() + timedelta(days=1)).strftime(
                        "%Y-%m-%d"
                    )
                else:
                    parsed = date_parser.parse(date_str, fuzzy=True)
                    info["date"] = parsed.strftime("%Y-%m-%d")
                break
            except:
                pass

    # Try to extract time - improved patterns
    # Pattern 1: HH:MM with optional am/pm
    time_pattern_1 = r"\b(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)?\b"
    match = re.search(time_pattern_1, message)
    if match:
        hour = int(match.group(1))
        minute = match.group(2)
        period = match.group(3)

        if period and period.lower() == "pm" and hour < 12:
            hour += 12
        elif period and period.lower() == "am" and hour == 12:
            hour = 0

        info["start_time"] = f"{hour:02d}:{minute}"
    else:
        # Pattern 2: Just hour (like "at 5" or "5 pm")
        time_pattern_2 = r"\bat\s+(\d{1,2})\s*(am|pm|AM|PM)?"
        match = re.search(time_pattern_2, message)
        if not match:
            # Also try without "at"
            time_pattern_2 = r"\b(\d{1,2})\s*(am|pm|AM|PM)\b"
            match = re.search(time_pattern_2, message)

        if match:
            hour = int(match.group(1))
            period = (
                match.group(2) if match.lastindex and match.lastindex >= 2 else None
            )

            # Default to PM for afternoon hours if no period specified
            if not period and 1 <= hour <= 11:
                # Assume PM for common times like 5 = 5pm
                hour += 12 if hour < 12 else 0
            elif period and period.lower() == "pm" and hour < 12:
                hour += 12
            elif period and period.lower() == "am" and hour == 12:
                hour = 0

            info["start_time"] = f"{hour:02d}:00"

    # Try to extract duration
    duration_pattern = r"(\d+)\s*(hour|hr|minute|min)s?"
    match = re.search(duration_pattern, message, re.IGNORECASE)
    if match:
        value = int(match.group(1))
        unit = match.group(2).lower()

        if "hour" in unit or unit == "hr":
            info["duration"] = value * 60
        else:
            info["duration"] = value

    # Title extraction - improved logic
    if not current_state.get("event_title"):
        # Look for activity patterns like "do yoga", "have meeting", "dentist appointment"
        activity_patterns = [
            r"(?:do|have|schedule|book|plan|attend|join)\s+(?:a\s+)?(\w+(?:\s+\w+)?)",
            r"(\w+(?:\s+\w+)?)\s+(?:appointment|meeting|session|class)",
        ]

        for pattern in activity_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # Capitalize properly
                info["title"] = title.title()
                break

        # If no pattern match and message is short, use the whole message
        if (
            not info.get("title")
            and len(message.split()) <= 10
            and not any(
                [info.get("date"), info.get("start_time"), info.get("duration")]
            )
        ):
            info["title"] = message.strip().title()

    return info
