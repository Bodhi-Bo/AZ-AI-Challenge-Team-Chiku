from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    Query,
    APIRouter,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
import json
import logging

from app.utils.mongo_client import init_db
from app.services.mongo_calendar_service import MongoCalendarService
from app.services.conversation_service import ConversationService


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(title="Calendar Assistant (Chiku - ReAct)", version="0.2.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create API router with /api prefix
api_router = APIRouter(prefix="/api")

# Store agent instances per user
# Initialize calendar service
calendar_service = MongoCalendarService()
conversation_service = ConversationService()


@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    logger.info("🚀 Starting Calendar Assistant application...")
    try:
        await init_db()
        logger.info("✅ Database initialization complete!")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}", exc_info=True)
        logger.warning(
            "⚠️  Continuing startup, but some features may not work correctly."
        )


from app.agents.react.react_agent import create_react_agent, ReactCalendarAgent

user_agents: Dict[str, ReactCalendarAgent] = {}


class ChatMessage(BaseModel):
    user_id: str
    text: str


class ChatResponse(BaseModel):
    reply: str


class CalendarEventResponse(BaseModel):
    """Response model for a single calendar event."""

    _id: str
    user_id: str
    title: str
    date: str
    start_time: str
    duration: int
    description: str | None
    event_datetime: str
    created_at: str
    updated_at: str


class CalendarEventsResponse(BaseModel):
    """Response model for calendar events in a date range."""

    user_id: str
    start_date: str
    end_date: str
    events: List[CalendarEventResponse]
    total: int


class ReminderResponse(BaseModel):
    """Response model for a single reminder."""

    _id: str
    user_id: str
    title: str
    reminder_datetime: str
    priority: str
    status: str
    event_id: str | None
    notes: str | None


class RemindersResponse(BaseModel):
    """Response model for upcoming reminders."""

    user_id: str
    hours_ahead: int
    reminders: List[ReminderResponse]
    total: int


class MessageResponse(BaseModel):
    """Response model for a single message."""

    _id: str
    role: str
    content: str
    timestamp: str


class ChatHistoryResponse(BaseModel):
    """Response model for chat history."""

    user_id: str
    messages: List[MessageResponse]
    total: int


@api_router.get("/health")
def health():
    return {"status": "ok"}


@api_router.post("/chat", response_model=ChatResponse)
async def chat(msg: ChatMessage):
    """
    Legacy REST endpoint for chat (kept for compatibility).
    WebSocket endpoint is recommended for better real-time interaction.
    """
    # Get or create agent for this user
    # Ensure we recreate the agent if the user_id doesn't match (prevents stale agent reuse)
    if (
        msg.user_id not in user_agents
        or user_agents[msg.user_id].user_id != msg.user_id
    ):
        if msg.user_id in user_agents:
            logger.warning(
                f"Recreating agent for {msg.user_id} - user_id mismatch detected"
            )
        user_agents[msg.user_id] = create_react_agent(msg.user_id)

    agent = user_agents[msg.user_id]

    # Process message
    response_text = await agent.chat(msg.text)

    return ChatResponse(reply=response_text)


@api_router.get("/events/{user_id}/range", response_model=CalendarEventsResponse)
async def get_events_range(
    user_id: str,
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
):
    """
    Get calendar events for a user within a date range.

    Args:
        user_id: User identifier
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        CalendarEventsResponse with events in the specified range
    """
    try:
        # Fetch events from the database
        events = await calendar_service.get_events_by_date_range(
            user_id=user_id, start_date=start_date, end_date=end_date
        )

        # Convert CalendarEvent documents to response format
        event_responses = [
            CalendarEventResponse(
                _id=str(event.id),
                user_id=event.user_id,
                title=event.title,
                date=event.date,
                start_time=event.start_time,
                duration=event.duration,
                description=event.description,
                event_datetime=event.event_datetime.isoformat(),
                created_at=event.created_at.isoformat(),
                updated_at=event.updated_at.isoformat(),
            )
            for event in events
        ]

        return CalendarEventsResponse(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            events=event_responses,
            total=len(event_responses),
        )

    except ValueError as e:
        # Handle invalid date format
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching events for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/reminders/{user_id}/upcoming", response_model=RemindersResponse)
async def get_upcoming_reminders(
    user_id: str,
    hours_ahead: int = Query(24, description="Number of hours to look ahead"),
):
    """
    Get upcoming reminders for a user within the next X hours.

    Args:
        user_id: User identifier
        hours_ahead: Number of hours to look ahead (default: 24)

    Returns:
        RemindersResponse with upcoming reminders
    """
    try:
        # Fetch reminders from the database
        reminders = await calendar_service.get_upcoming_reminders(
            user_id=user_id, hours_ahead=hours_ahead
        )

        # Convert Reminder documents to response format
        reminder_responses = [
            ReminderResponse(
                _id=str(reminder.id),
                user_id=reminder.user_id,
                title=reminder.title,
                reminder_datetime=reminder.reminder_datetime.isoformat(),
                priority=reminder.priority,
                status=reminder.status,
                event_id=reminder.event_id,
                notes=reminder.notes,
            )
            for reminder in reminders
        ]

        return RemindersResponse(
            user_id=user_id,
            hours_ahead=hours_ahead,
            reminders=reminder_responses,
            total=len(reminder_responses),
        )

    except Exception as e:
        logger.error(f"Error fetching reminders for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.get("/messages/{user_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    user_id: str,
    limit: int = Query(50, description="Maximum number of messages to return"),
):
    """
    Get chat message history for a user.

    Args:
        user_id: User identifier
        limit: Maximum number of messages to return (default: 50)

    Returns:
        ChatHistoryResponse with message history
    """
    try:
        # Fetch messages from the database
        messages = await conversation_service.get_recent_messages(
            user_id=user_id, limit=limit
        )

        # Convert Message documents to response format
        message_responses = [
            MessageResponse(
                _id=msg.id or "",
                role=msg.role,
                content=msg.content,
                timestamp=msg.created_at.isoformat(),
            )
            for msg in messages
        ]

        return ChatHistoryResponse(
            user_id=user_id, messages=message_responses, total=len(message_responses)
        )

    except Exception as e:
        logger.error(
            f"Error fetching chat history for user {user_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@api_router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time chat with Chiku, the calendar assistant.

    Message format (from client):
    {"type": "message", "text": "user message here"}

    Response format (to client):
    {"type": "response", "text": "assistant response"}
    """
    await websocket.accept()
    logger.info(f"🔗 WebSocket connection established for user: {user_id}")

    # Get or create agent for this user
    # Ensure we recreate the agent if the user_id doesn't match (prevents stale agent reuse)
    if user_id not in user_agents or user_agents[user_id].user_id != user_id:
        if user_id in user_agents:
            logger.warning(
                f"Recreating agent for {user_id} - user_id mismatch detected"
            )
        user_agents[user_id] = create_react_agent(user_id)

    agent = user_agents[user_id]

    try:
        # Send welcome message
        await websocket.send_json(
            {
                "type": "response",
                "text": "👋 Hi! I'm Chiku, your compassionate calendar assistant. I'm here to help you manage your schedule in a way that works for you. What would you like to do today?",
            }
        )

        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data.get("type") == "message":
                user_message = message_data.get("text", "")

                logger.info("*" * 80)
                logger.info(f"📨 Received message from user {user_id}: {user_message}")
                logger.info("*" * 80)

                # Process with ReAct agent
                response_text = await agent.chat(user_message)

                # Send response back to client
                logger.info(f"📤 Sending response to user: {response_text}")
                logger.info("*" * 80)
                await websocket.send_json({"type": "response", "text": response_text})

            elif message_data.get("type") == "ping":
                # Respond to ping to keep connection alive
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"🔌 Client {user_id} disconnected")
        # Keep agent in memory for reconnection
    except Exception as e:
        logger.error(
            f"❌ Error in WebSocket connection for {user_id}: {e}", exc_info=True
        )
        await websocket.close()


# Include the API router
app.include_router(api_router)
