#!/usr/bin/env python3
"""
Complete Dummy Backend for Chiku AI Assistant
Provides both WebSocket (for chat) and REST APIs (for data fetching).

Usage:
    python server.py

WebSocket: ws://localhost:8000/ws/{user_id}
REST APIs:
    GET http://localhost:8000/api/messages/{user_id}?limit=50
    GET http://localhost:8000/api/events/{user_id}/range?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    GET http://localhost:8000/api/reminders/{user_id}/upcoming?hours_ahead=24
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================
# MOCK DATA STORAGE
# ============================================
calendar_events: Dict[str, List[dict]] = {}
conversation_history: Dict[str, List[dict]] = {}
reminders: Dict[str, List[dict]] = {}


def initialize_mock_data():
    """Initialize with sample data for testing."""
    user_id = "user_123"
    today = datetime.now()

    # Sample events
    calendar_events[user_id] = [
        {
            "_id": "evt_1",
            "user_id": user_id,
            "title": "Team Standup",
            "date": today.strftime("%Y-%m-%d"),
            "start_time": "09:00",
            "duration": 30,
            "description": "Daily team sync",
            "event_datetime": f"{today.strftime('%Y-%m-%d')}T09:00:00Z",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "_id": "evt_2",
            "user_id": user_id,
            "title": "Lunch Break",
            "date": today.strftime("%Y-%m-%d"),
            "start_time": "12:00",
            "duration": 60,
            "event_datetime": f"{today.strftime('%Y-%m-%d')}T12:00:00Z",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "_id": "evt_3",
            "user_id": user_id,
            "title": "Dentist Appointment",
            "date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
            "start_time": "14:00",
            "duration": 45,
            "description": "Regular checkup",
            "event_datetime": f"{(today + timedelta(days=1)).strftime('%Y-%m-%d')}T14:00:00Z",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "_id": "evt_4",
            "user_id": user_id,
            "title": "Gym Session",
            "date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
            "start_time": "18:00",
            "duration": 60,
            "event_datetime": f"{(today + timedelta(days=2)).strftime('%Y-%m-%d')}T18:00:00Z",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]

    # Sample conversation history
    conversation_history[user_id] = [
        {
            "_id": "msg_1",
            "role": "user",
            "content": "Hi Chiku!",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
        },
        {
            "_id": "msg_2",
            "role": "assistant",
            "content": "👋 Hi! I'm Chiku, your ADHD-friendly calendar assistant. How can I help you today?",
            "timestamp": (datetime.now() - timedelta(hours=2, seconds=5)).isoformat()
        },
        {
            "_id": "msg_3",
            "role": "user",
            "content": "What's on my schedule today?",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat()
        },
        {
            "_id": "msg_4",
            "role": "assistant",
            "content": "You have 2 events today:\n1. Team Standup at 09:00 (30 min)\n2. Lunch Break at 12:00 (60 min)",
            "timestamp": (datetime.now() - timedelta(hours=1, seconds=-3)).isoformat()
        }
    ]

    # Sample reminders
    reminders[user_id] = [
        {
            "_id": "rem_1",
            "user_id": user_id,
            "title": "Team standup starting soon",
            "reminder_datetime": (datetime.now() + timedelta(minutes=15)).isoformat(),
            "priority": "high",
            "status": "pending",
            "event_id": "evt_1",
            "notes": "Don't forget your notes!"
        },
        {
            "_id": "rem_2",
            "user_id": user_id,
            "title": "Dentist appointment tomorrow",
            "reminder_datetime": (datetime.now() + timedelta(hours=12)).isoformat(),
            "priority": "normal",
            "status": "pending",
            "event_id": "evt_3",
            "notes": "Bring insurance card"
        }
    ]

    logger.info("✅ Mock data initialized")


# ============================================
# REST API HANDLER
# ============================================
class RESTAPIHandler(BaseHTTPRequestHandler):
    """Handle REST API requests."""

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.split('/')
        query_params = parse_qs(parsed_path.query)

        try:
            # GET /api/messages/{user_id}
            if len(path_parts) >= 4 and path_parts[1] == 'api' and path_parts[2] == 'messages':
                user_id = path_parts[3]
                limit = int(query_params.get('limit', [50])[0])

                msgs = conversation_history.get(user_id, [])[-limit:]
                response = {
                    "user_id": user_id,
                    "messages": msgs,
                    "total": len(msgs)
                }

                self.send_json_response(response)
                logger.info(f"📨 GET /api/messages/{user_id} - Sent {len(msgs)} messages")

            # GET /api/events/{user_id}/range
            elif len(path_parts) >= 5 and path_parts[1] == 'api' and path_parts[2] == 'events' and path_parts[4] == 'range':
                user_id = path_parts[3]
                start_date = query_params.get('start_date', [''])[0]
                end_date = query_params.get('end_date', [''])[0]

                all_events = calendar_events.get(user_id, [])

                # Filter events by date range
                if start_date and end_date:
                    filtered_events = [
                        evt for evt in all_events
                        if start_date <= evt['date'] <= end_date
                    ]
                else:
                    filtered_events = all_events

                response = {
                    "user_id": user_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "events": filtered_events,
                    "total": len(filtered_events)
                }

                self.send_json_response(response)
                logger.info(f"📅 GET /api/events/{user_id}/range - Sent {len(filtered_events)} events ({start_date} to {end_date})")

            # GET /api/reminders/{user_id}/upcoming
            elif len(path_parts) >= 5 and path_parts[1] == 'api' and path_parts[2] == 'reminders' and path_parts[4] == 'upcoming':
                user_id = path_parts[3]
                hours_ahead = int(query_params.get('hours_ahead', [24])[0])

                all_reminders = reminders.get(user_id, [])

                # Filter upcoming reminders
                now = datetime.now()
                future = now + timedelta(hours=hours_ahead)

                upcoming = [
                    rem for rem in all_reminders
                    if rem['status'] == 'pending' and
                       now.isoformat() <= rem['reminder_datetime'] <= future.isoformat()
                ]

                response = {
                    "user_id": user_id,
                    "hours_ahead": hours_ahead,
                    "reminders": upcoming,
                    "total": len(upcoming)
                }

                self.send_json_response(response)
                logger.info(f"🔔 GET /api/reminders/{user_id}/upcoming - Sent {len(upcoming)} reminders")

            else:
                self.send_error(404, "Endpoint not found")

        except Exception as e:
            logger.error(f"Error handling GET request: {e}")
            self.send_error(500, str(e))

    def send_json_response(self, data):
        """Send JSON response with CORS headers."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        """Suppress default HTTP logging."""
        pass


def start_rest_api_server():
    """Start HTTP server for REST APIs."""
    server_address = ('localhost', 8001)
    httpd = HTTPServer(server_address, RESTAPIHandler)
    logger.info(f"📡 REST API server: http://localhost:8001/api/")
    httpd.serve_forever()


# ============================================
# WEBSOCKET LOGIC (Chat)
# ============================================
def create_mock_event(user_id: str, title: str, date: str, time: str, duration: int) -> dict:
    """Create a mock calendar event."""
    event_id = f"evt_{len(calendar_events.get(user_id, [])) + 1}"
    event = {
        "_id": event_id,
        "user_id": user_id,
        "title": title,
        "date": date,
        "start_time": time,
        "duration": duration,
        "event_datetime": f"{date}T{time}:00Z",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    if user_id not in calendar_events:
        calendar_events[user_id] = []
    calendar_events[user_id].append(event)

    return event


def get_mock_response(user_id: str, message: str) -> str:
    """Generate mock AI responses based on user message."""
    msg_lower = message.lower()

    # Intent: Create event
    if any(word in msg_lower for word in ["schedule", "create", "add", "book", "set up"]):
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        event = create_mock_event(user_id, "Team Meeting", tomorrow, "14:00", 60)
        return f"✅ Perfect! I've scheduled '{event['title']}' for {event['date']} at {event['start_time']} for {event['duration']} minutes."

    # Intent: Get schedule
    elif any(word in msg_lower for word in ["what's", "show", "list", "schedule", "events"]):
        events = calendar_events.get(user_id, [])
        if not events:
            return "You don't have any events scheduled yet. Would you like to add one?"

        response = f"You have {len(events)} event(s):\n\n"
        for i, evt in enumerate(events, 1):
            response += f"{i}. {evt['title']} on {evt['date']} at {evt['start_time']} ({evt['duration']} min)\n"
        return response

    # Intent: Delete/cancel
    elif any(word in msg_lower for word in ["delete", "cancel", "remove"]):
        if user_id in calendar_events and calendar_events[user_id]:
            removed = calendar_events[user_id].pop()
            return f"✅ I've removed '{removed['title']}' from your calendar."
        return "You don't have any events to remove."

    # Intent: Help/overwhelmed
    elif any(word in msg_lower for word in ["help", "overwhelmed", "stressed", "anxious"]):
        return "I understand you're feeling overwhelmed. Let's break things down together. Would you like me to:\n\n1. Show your schedule for today\n2. Help prioritize your tasks\n3. Suggest which events you could reschedule\n\nWhat would be most helpful right now?"

    # Intent: Greeting
    elif any(word in msg_lower for word in ["hello", "hi", "hey"]):
        return "👋 Hi! I'm Chiku, your ADHD-friendly calendar assistant. I'm here to help you manage your schedule in a compassionate way. What would you like to do?"

    # Intent: Thanks
    elif any(word in msg_lower for word in ["thank", "thanks"]):
        return "You're welcome! I'm always here to help. Is there anything else you'd like to do? 😊"

    # Default: General response
    else:
        return "I'm here to help you with your calendar! You can ask me to:\n• Schedule events\n• View your schedule\n• Reschedule tasks\n• Get reminders\n\nWhat would you like to do?"


async def handle_websocket(websocket):  # ✅ New signature (no path parameter)
    """Handle WebSocket connections for chat."""
    # ✅ Get path from websocket.request.path
    path = websocket.request.path
    user_id = path.split('/')[-1] if '/' in path else "anonymous"
    logger.info(f"🔗 WebSocket connected: {user_id}")

    try:
        # Send welcome message
        welcome_msg = {
            "type": "response",
            "text": "👋 Hi! I'm Chiku, your compassionate calendar assistant. I'm here to help you manage your schedule in a way that works for you. What would you like to do today?"
        }
        await websocket.send(json.dumps(welcome_msg))

        # Message loop
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == "message":
                    user_text = data.get("text", "")
                    logger.info(f"💬 {user_id}: {user_text}")

                    # Store in conversation history
                    if user_id not in conversation_history:
                        conversation_history[user_id] = []
                    conversation_history[user_id].append({
                        "_id": f"msg_{len(conversation_history[user_id]) + 1}",
                        "role": "user",
                        "content": user_text,
                        "timestamp": datetime.now().isoformat()
                    })

                    # Simulate AI thinking delay
                    await asyncio.sleep(0.5)

                    # Generate response
                    response_text = get_mock_response(user_id, user_text)

                    # Store AI response
                    conversation_history[user_id].append({
                        "_id": f"msg_{len(conversation_history[user_id]) + 1}",
                        "role": "assistant",
                        "content": response_text,
                        "timestamp": datetime.now().isoformat()
                    })

                    # Send response
                    response_msg = {"type": "response", "text": response_text}
                    await websocket.send(json.dumps(response_msg))
                    logger.info(f"📤 Sent response to {user_id}")

                elif msg_type == "ping":
                    pong_msg = {"type": "pong"}
                    await websocket.send(json.dumps(pong_msg))
                    logger.debug(f"🏓 Pong -> {user_id}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {user_id}")

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"🔌 {user_id} disconnected")
    except Exception as e:
        logger.error(f"❌ Error with {user_id}: {e}")


async def start_websocket_server():
    """Start WebSocket server for chat."""
    async with websockets.serve(handle_websocket, "localhost", 8000):
        logger.info("📡 WebSocket server: ws://localhost:8000/ws/{user_id}")
        await asyncio.Future()  # Run forever


# ============================================
# MAIN
# ============================================
async def main():
    """Start both servers."""
    logger.info("=" * 80)
    logger.info("🚀 Starting Chiku Dummy Backend")
    logger.info("=" * 80)

    # Initialize mock data
    initialize_mock_data()

    # Start REST API server in separate thread
    rest_thread = threading.Thread(target=start_rest_api_server, daemon=True)
    rest_thread.start()

    logger.info("💡 WebSocket Example: ws://localhost:8000/ws/user_123")
    logger.info("💡 REST Example: http://localhost:8001/api/messages/user_123")
    logger.info("=" * 80)
    logger.info("✅ All servers running! Press Ctrl+C to stop.")
    logger.info("=" * 80)

    # Start WebSocket server
    await start_websocket_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Servers stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
