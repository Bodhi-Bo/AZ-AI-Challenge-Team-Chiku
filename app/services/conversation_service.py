"""
Service for managing conversation messages and state.
Stores message history in MongoDB and manages in-memory conversation state.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class Message(BaseModel):
    """Represents a conversation message."""

    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    role: str  # "user" or "assistant"
    content: str

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class ConversationState(BaseModel):
    """Represents the current working state of a conversation."""

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

        message_dict = {
            "user_id": user_id,
            "timestamp": datetime.now(),
            "role": role,
            "content": content,
        }

        result = await messages.insert_one(message_dict)
        message_dict["_id"] = str(result.inserted_id)

        return Message(**message_dict)

    async def get_recent_messages(self, user_id: str, limit: int = 5) -> List[Message]:
        """Get the most recent messages for a user."""
        from app.utils.mongo_client import get_mongo_database

        db = await get_mongo_database()
        messages = db.messages

        cursor = messages.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)

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

        # Update the in-memory state
        self.conversation_states[user_id] = ConversationState(**state_dict)
        return self.conversation_states[user_id]

    def reset_conversation_state(self, user_id: str) -> None:
        """Reset the conversation state for a user."""
        self.conversation_states[user_id] = ConversationState()

    def reset_transient_state(self, user_id: str) -> None:
        """
        Reset only transient conversation state, preserving user_profile.
        Called when starting a new conversation after a declarative message.
        """
        current_state = self.get_conversation_state(user_id)
        preserved_profile = current_state.user_profile.copy()

        # Reset to fresh state but keep the profile
        self.conversation_states[user_id] = ConversationState(
            user_profile=preserved_profile
        )

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
