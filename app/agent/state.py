from typing import TypedDict, Literal, Optional
from datetime import datetime


class AgentState(TypedDict):
    """State for the calendar assistant agent."""

    # Conversation context
    messages: list[dict]  # Chat history
    user_id: str

    # Intent classification
    intent: Optional[Literal["calendar_event", "casual_chat", "unknown"]]

    # Calendar event details being gathered
    event_title: Optional[str]
    event_date: Optional[str]  # ISO format YYYY-MM-DD
    event_start_time: Optional[str]  # HH:MM format
    event_duration: Optional[int]  # in minutes

    # Control flow
    next_action: Optional[
        Literal["classify", "gather_info", "create_event", "chat", "end"]
    ]
    response: Optional[str]  # Agent's response to send to user
