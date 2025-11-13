from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict
import json
import logging

from app.utils.mongo_client import init_db


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(title="Calendar Assistant (Chiku - ReAct)", version="0.2.0")

# Store agent instances per user


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


from app.agent.react_agent import create_react_agent, ReactCalendarAgent

user_agents: Dict[str, ReactCalendarAgent] = {}


class ChatMessage(BaseModel):
    user_id: str
    text: str


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
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


@app.websocket("/ws/{user_id}")
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
