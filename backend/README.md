# Calendar Assistant Chatbot

A FastAPI-based chatbot that uses LangGraph to intelligently handle calendar event creation and casual conversation over WebSockets.

## Features

- **WebSocket Real-time Chat**: Bi-directional communication with the assistant
- **Intent Classification**: Automatically detects if user wants to create a calendar event or just chat
- **Intelligent Info Gathering**: Recursively collects all necessary event details (title, date, time, duration)
- **Natural Language Understanding**: Extracts event details from natural conversation
- **Stateful Conversations**: Maintains context across multiple messages per user

## Architecture

The app uses **LangGraph** to create a state machine with the following flow:

```
User Message → Classify Intent → Calendar Event | Casual Chat
                                      ↓              ↓
                                 Gather Info    → Response
                                      ↓
                              Create Event → Confirmation
```

### Components

- `app/main.py`: FastAPI server with WebSocket endpoint
- `app/agent/`: LangGraph state machine implementation
  - `graph.py`: State machine definition
  - `nodes.py`: Agent nodes (classify, gather_info, create_event, chat)
  - `state.py`: Conversation state schema
  - `tools.py`: Tool definitions
- `app/services/calendar_service.py`: In-memory calendar storage
- `app/config.py`: Configuration and prompts

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure OpenAI API**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Run the server**:
   ```bash
   uvicorn app.main:app --reload
   ```

## Usage

### WebSocket Client Example

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/user123');

ws.onopen = () => {
  console.log('Connected');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Assistant:', data.text);
};

// Send a message
ws.send(JSON.stringify({
  type: 'message',
  text: 'Schedule a team meeting tomorrow at 2pm for 1 hour'
}));
```

### REST API (Legacy)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "text": "Hello!"}'
```

## Example Conversations

**Creating a calendar event:**
```
User: I need to schedule a dentist appointment
Bot: Sure! When would you like to schedule the dentist appointment?
User: Tomorrow at 2pm
Bot: Got it! How long will the appointment be?
User: 30 minutes
Bot: ✅ Perfect! I've created your dentist appointment for [date] at 14:00 for 30 minutes.
```

**Casual chat:**
```
User: What's the weather like?
Bot: I'm a calendar assistant, so I don't have weather information. But I'd be happy to help you schedule events!
```

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: Model to use (default: `gpt-4`)

## API Endpoints

- `GET /health`: Health check
- `POST /chat`: REST endpoint for chat
- `WS /ws/{user_id}`: WebSocket endpoint for real-time chat
