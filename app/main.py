from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict
import json
import logging
from app.agent.autonomous_agent import create_autonomous_agent, AutonomousCalendarAgent

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(title="Calendar Assistant", version="0.1.0")

# Store agent instances per user
user_agents: Dict[str, AutonomousCalendarAgent] = {}


class ChatMessage(BaseModel):
    user_id: str
    text: str


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(msg: ChatMessage):
    """
    Legacy REST endpoint for chat (kept for compatibility).
    WebSocket endpoint is recommended for better real-time interaction.
    """
    # Get or create agent for this user
    if msg.user_id not in user_agents:
        user_agents[msg.user_id] = create_autonomous_agent(msg.user_id)

    agent = user_agents[msg.user_id]

    # Process message
    response_text = agent.chat(msg.text)

    return ChatResponse(reply=response_text)


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time chat with the calendar assistant.

    Message format (from client):
    {"type": "message", "text": "user message here"}

    Response format (to client):
    {"type": "response", "text": "assistant response"}
    """
    await websocket.accept()
    logger.info(f"🔗 WebSocket connection established for user: {user_id}")

    # Get or create agent for this user
    if user_id not in user_agents:
        user_agents[user_id] = create_autonomous_agent(user_id)

    agent = user_agents[user_id]

    try:
        # Send welcome message
        await websocket.send_json(
            {
                "type": "response",
                "text": "👋 Hi! I'm your calendar assistant. I can help you create, view, update, or delete calendar events. What can I do for you today?",
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

                # Process with autonomous agent
                response_text = agent.chat(user_message)

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
