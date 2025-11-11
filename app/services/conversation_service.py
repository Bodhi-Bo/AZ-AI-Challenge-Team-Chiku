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

    intent: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    planning: Optional[Dict[str, Any]] = None
    commitments: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    reasoning: str = ""


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
