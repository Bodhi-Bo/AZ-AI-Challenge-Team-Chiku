"""
Service for managing conversation messages and state.
Stores message history in MongoDB and manages in-memory conversation state.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
from pydantic import BaseModel, Field
from bson import ObjectId

logger = logging.getLogger(__name__)


class Message(BaseModel):
    """Represents a conversation message."""

    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    session_id: str  # Groups messages by conversation session
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    role: str  # "user" or "assistant"
    content: str
    is_old: bool = False  # Marks messages from completed conversations

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class ConversationState(BaseModel):
    """Represents the current working state of a conversation."""

    # Session tracking
    session_id: Optional[str] = None  # Current conversation session ID

    # PERSISTENT across conversations - learnings about the user
    user_profile: Dict[str, Any] = Field(default_factory=dict)

    # TRANSIENT - reset when new conversation starts
    intent: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    planning: Optional[Dict[str, Any]] = None
    commitments: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    reasoning: str = ""

    # Track last iteration's tool calls for prompt population
    last_tool_calls: List[Dict[str, Any]] = Field(default_factory=list)

    # Allow any additional custom fields the LLM wants to store
    class Config:
        extra = "allow"  # Allow arbitrary fields


class ConversationService:
    """MongoDB-backed conversation service."""

    def __init__(self):
        """Initialize conversation service."""
        # In-memory conversation states (user_id -> ConversationState)
        self.conversation_states: Dict[str, ConversationState] = {}

    async def save_message(self, user_id: str, role: str, content: str) -> Message:
        """Save a message to the conversation history."""
        from app.utils.mongo_client import get_mongo_database

        db = await get_mongo_database()
        messages = db.messages

        # Get current session_id from conversation state
        current_state = self.get_conversation_state(user_id)
        session_id = current_state.session_id

        # If no session_id exists, create one (first message ever)
        if not session_id:
            session_id = str(ObjectId())
            current_state.session_id = session_id
            self.conversation_states[user_id] = current_state

        now = datetime.now()
        message_dict = {
            "user_id": user_id,
            "session_id": session_id,
            "created_at": now,
            "updated_at": now,
            "role": role,
            "content": content,
            "is_old": False,
        }

        result = await messages.insert_one(message_dict)
        message_dict["_id"] = str(result.inserted_id)

        return Message(**message_dict)

    async def get_recent_messages(self, user_id: str, limit: int = 5) -> List[Message]:
        """Get the most recent messages for a user that are not marked as old."""
        from app.utils.mongo_client import get_mongo_database

        db = await get_mongo_database()
        messages = db.messages

        cursor = (
            messages.find(
                {
                    "user_id": user_id,
                    "is_old": False,  # Only get current conversation messages
                }
            )
            .sort("created_at", -1)
            .limit(limit)
        )

        # Reverse to get chronological order (oldest to newest)
        messages_list = []
        async for msg in cursor:
            messages_list.append(Message(**{**msg, "_id": str(msg["_id"])}))

        return list(reversed(messages_list))

    def get_conversation_state(self, user_id: str) -> ConversationState:
        """Get the current conversation state for a user."""
        if user_id not in self.conversation_states:
            self.conversation_states[user_id] = ConversationState()
        return self.conversation_states[user_id]

    def get_conversation_state_for_prompt(self, user_id: str) -> Dict[str, Any]:
        """
        Get conversation state as dict for prompt inclusion.
        Excludes last_tool_calls to avoid duplication with last_tool_actions_and_result.
        """
        state = self.get_conversation_state(user_id)
        state_dict = state.dict()
        # Remove last_tool_calls as it's formatted separately
        state_dict.pop("last_tool_calls", None)
        return state_dict

    def update_conversation_state(
        self, user_id: str, partial_update: Dict[str, Any]
    ) -> ConversationState:
        """
        Merge a partial state update into the current conversation state.
        Uses deep merging to preserve existing fields not mentioned in the update.
        """
        current_state = self.get_conversation_state(user_id)
        state_dict = current_state.dict()

        # Deep merge the partial update
        state_dict = self._deep_merge(state_dict, partial_update)
        logger.info(
            f"[CONVERSATION SERVICE] Updated state for user {user_id}: final state\n{state_dict}"
        )

        # Update the in-memory state
        self.conversation_states[user_id] = ConversationState(**state_dict)
        return self.conversation_states[user_id]

    def reset_conversation_state(self, user_id: str) -> None:
        """Reset the conversation state for a user."""
        self.conversation_states[user_id] = ConversationState()

    async def reset_transient_state(self, user_id: str) -> Dict[str, Any]:
        """
        Reset only transient conversation state, preserving user_profile.
        Called when starting a new conversation after a declarative message.
        Also marks all messages from current session as old and generates new session_id.

        Returns:
            dict: Information about the reset including messages_marked_old and new_session_id
        """
        current_state = self.get_conversation_state(user_id)
        preserved_profile = current_state.user_profile.copy()
        current_session_id = current_state.session_id

        # Mark all messages from current session as old
        messages_marked_old = 0
        if current_session_id:
            messages_marked_old = await self.mark_messages_as_old(
                user_id, current_session_id
            )

        # Generate new session_id for next conversation
        new_session_id = str(ObjectId())

        # Reset to fresh state but keep the profile and assign new session
        self.conversation_states[user_id] = ConversationState(
            user_profile=preserved_profile, session_id=new_session_id
        )

        return {
            "messages_marked_old": messages_marked_old,
            "new_session_id": new_session_id,
        }

    async def mark_messages_as_old(self, user_id: str, session_id: str) -> int:
        """
        Mark all messages from a specific session as old.
        Returns the count of messages updated.
        """
        from app.utils.mongo_client import get_mongo_database

        db = await get_mongo_database()
        messages = db.messages

        result = await messages.update_many(
            {"user_id": user_id, "session_id": session_id, "is_old": False},
            {"$set": {"is_old": True, "updated_at": datetime.now()}},
        )

        return result.modified_count

    def _deep_merge(
        self, base: Dict[str, Any], update: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.
        Values in 'update' override values in 'base'.
        """
        result = base.copy()

        for key, value in update.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    async def format_recent_messages(self, user_id: str, limit: int = 5) -> str:
        """Format recent messages as a string for prompt inclusion."""
        messages = await self.get_recent_messages(user_id, limit)

        if not messages:
            return "No previous messages."

        formatted = []
        for msg in messages:
            formatted.append(f"{msg.role}: {msg.content}")

        return "\n".join(formatted)


# Global instance
conversation_service = ConversationService()
