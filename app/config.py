import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

# Agent Prompts
CLASSIFIER_PROMPT = """You are a helpful assistant that classifies user intent based on conversation context.

Conversation context:
{context}

Analyze the user's latest message in the context of the conversation and determine if they want to:
1. Create a calendar event (scheduling, appointments, meetings, reminders, answering questions about event details like time/duration/date)
2. Have a casual conversation (general questions, greetings, chit-chat unrelated to scheduling)

IMPORTANT: If the user is answering a question about event details (like "30 minutes" for duration, "yes" to confirm, etc.), classify as "calendar_event".

Respond with ONLY one word: "calendar_event" or "casual_chat"

Latest user message: {user_message}

Classification:"""

INFO_GATHERER_PROMPT = """You are a helpful calendar assistant gathering event details.

Current event information collected:
- Title: {title}
- Date: {date}
- Start Time: {start_time}
- Duration: {duration} minutes

Required fields: title, date (YYYY-MM-DD), start_time (HH:MM), duration (in minutes)

Analyze what's missing and ask the user for ONE piece of missing information in a friendly way.
If you have information from the conversation, extract it.

User's latest message: {user_message}

Your response:"""

EVENT_CREATOR_PROMPT = """You are confirming a calendar event creation.

Event details:
- Title: {title}
- Date: {date}
- Start Time: {start_time}
- Duration: {duration} minutes

Generate a friendly confirmation message that the event has been created successfully.

Your response:"""

CASUAL_CHAT_PROMPT = """You are a friendly and helpful calendar assistant.

The user is having a casual conversation with you. Respond naturally and helpfully.
Keep responses concise and friendly.

User message: {user_message}

Your response:"""
