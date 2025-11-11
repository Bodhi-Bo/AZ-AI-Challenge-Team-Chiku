"""
Autonomous agent that uses tool calling to manage calendar events.
No predefined graph - the LLM decides what to do next.
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
import logging
from typing import List, Dict, Any
from app.agent.mongo_tools import (
    get_events,
    get_events_on_date,
    get_todays_schedule,
    get_tomorrows_schedule,
    get_week_schedule,
    find_available_slots,
    check_time_availability,
    create_calendar_event,
    update_calendar_event,
    move_event_to_date,
    delete_calendar_event,
    create_reminder,
    create_reminder_for_event,
    get_upcoming_reminders,
    get_pending_reminders,
    mark_reminder_completed,
    snooze_reminder,
    delete_reminder,
)
from app.config import OPENAI_API_KEY, OPENAI_MODEL

# Configure logging
logger = logging.getLogger(__name__)

# System prompt for the autonomous agent
SYSTEM_PROMPT = """You are a helpful calendar assistant powered by semantic tools. You help users manage their calendar events and reminders intelligently.

You have access to these semantic tools:

**Calendar Query Tools:**
- get_events: Get events in a date range
- get_events_on_date: Get events for a specific date
- get_todays_schedule: Get today's events
- get_tomorrows_schedule: Get tomorrow's events  
- get_week_schedule: Get next 7 days of events

**Availability Tools:**
- find_available_slots: Find free time slots on a date for a given duration
- check_time_availability: Check if a specific time slot is free

**Event Management Tools:**
- create_calendar_event: Create a new event
- update_calendar_event: Update any field of an event
- move_event_to_date: Move an event to a different date/time
- delete_calendar_event: Delete an event

**Reminder Tools:**
- create_reminder: Create a standalone reminder (not linked to event)
- create_reminder_for_event: Create reminder X minutes before an event
- get_upcoming_reminders: Get reminders in next X hours
- get_pending_reminders: Get all pending reminders
- mark_reminder_completed: Mark reminder as done
- snooze_reminder: Delay a reminder by X minutes
- delete_reminder: Delete a reminder

IMPORTANT - When users ask to reschedule or reprioritize tasks, follow this EXACT workflow:
1. Use get_events or get_events_on_date to see their current schedule
2. Use find_available_slots or get_events to check availability on other dates
3. Present a detailed plan of what you suggest moving/changing
4. Wait for user confirmation (like "yes", "do it", "sounds good", "go ahead", etc.)
5. When confirmed, IMMEDIATELY:
   - Use move_event_to_date or update_calendar_event for EACH event you're moving
   - Use get_events again to retrieve the updated schedule
   - Show them the final result with before/after comparison
6. If user rejects or wants changes, ask what they'd prefer and suggest alternatives

CRITICAL: After user confirms, you MUST actually execute the changes using the tools, not just say you will.
After making changes, ALWAYS show the updated schedule by calling the appropriate get_events tool.

Handle partial confirmations: If user says "move X but keep Y", respect their preferences.

Use semantic tools intelligently:
- Use get_todays_schedule instead of get_events when user asks about "today"
- Use find_available_slots when user needs to schedule something but doesn't specify a time
- Use move_event_to_date for clarity when moving events to different dates
- Use create_reminder_for_event when user wants to be reminded about an event
- Suggest creating reminders proactively for important events

Be conversational and helpful. Always show the results of actions you take.

Current date: 2025-11-10
"""


class AutonomousCalendarAgent:
    """
    Autonomous agent that uses LLM tool calling to manage calendar events.
    The LLM decides which tools to call and when.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0.7)

        # Bind tools to the LLM
        self.tools = [
            # Calendar query tools
            get_events,
            get_events_on_date,
            get_todays_schedule,
            get_tomorrows_schedule,
            get_week_schedule,
            # Availability tools
            find_available_slots,
            check_time_availability,
            # Event management tools
            create_calendar_event,
            update_calendar_event,
            move_event_to_date,
            delete_calendar_event,
            # Reminder tools
            create_reminder,
            create_reminder_for_event,
            get_upcoming_reminders,
            get_pending_reminders,
            mark_reminder_completed,
            snooze_reminder,
            delete_reminder,
        ]
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Conversation history
        self.messages: List[Any] = [SystemMessage(content=SYSTEM_PROMPT)]

        logger.info(f"Initialized autonomous agent for user: {user_id}")

    def chat(self, user_message: str) -> str:
        """
        Process a user message and return the agent's response.
        The agent autonomously decides which tools to call.
        """
        logger.info("=" * 80)
        logger.info(f"USER: {user_message}")

        # Add user message to history
        self.messages.append(HumanMessage(content=user_message))

        # Agent loop - keep going until LLM responds without tool calls
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"\n--- Iteration {iteration} ---")

            # Call LLM
            response = self.llm_with_tools.invoke(self.messages)
            self.messages.append(response)

            # Check if LLM wants to use tools
            if not response.tool_calls:
                # No tools called - LLM is responding to user
                content = str(response.content) if response.content else ""
                logger.info(f"AGENT: {content}")
                logger.info("=" * 80)
                return content

            # Execute tool calls
            logger.info(f"Tool calls requested: {len(response.tool_calls)}")

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                logger.info(f"\nCalling tool: {tool_name}")
                logger.info(f"Arguments: {tool_args}")

                # Inject user_id for all calendar tools if not present
                if "user_id" not in tool_args:
                    tool_args["user_id"] = self.user_id

                # Find and execute the tool
                tool_result = self._execute_tool(tool_name, tool_args)

                logger.info(f"Tool result: {tool_result}")

                # Add tool result to messages
                self.messages.append(
                    ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call["id"],
                    )
                )

        # Safety fallback if we hit max iterations
        logger.warning(f"Hit max iterations ({max_iterations})")
        return "I apologize, but I'm having trouble processing your request. Could you please rephrase?"

    def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """Execute a tool by name with given arguments."""
        tool_map = {
            # Calendar query tools
            "get_events": get_events,
            "get_events_on_date": get_events_on_date,
            "get_todays_schedule": get_todays_schedule,
            "get_tomorrows_schedule": get_tomorrows_schedule,
            "get_week_schedule": get_week_schedule,
            # Availability tools
            "find_available_slots": find_available_slots,
            "check_time_availability": check_time_availability,
            # Event management tools
            "create_calendar_event": create_calendar_event,
            "update_calendar_event": update_calendar_event,
            "move_event_to_date": move_event_to_date,
            "delete_calendar_event": delete_calendar_event,
            # Reminder tools
            "create_reminder": create_reminder,
            "create_reminder_for_event": create_reminder_for_event,
            "get_upcoming_reminders": get_upcoming_reminders,
            "get_pending_reminders": get_pending_reminders,
            "mark_reminder_completed": mark_reminder_completed,
            "snooze_reminder": snooze_reminder,
            "delete_reminder": delete_reminder,
        }

        tool = tool_map.get(tool_name)
        if not tool:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            result = tool.invoke(tool_args)
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return {"error": str(e)}

    def reset_conversation(self):
        """Reset the conversation history."""
        self.messages = [SystemMessage(content=SYSTEM_PROMPT)]
        logger.info("Conversation reset")


def create_autonomous_agent(user_id: str) -> AutonomousCalendarAgent:
    """Factory function to create an autonomous agent."""
    return AutonomousCalendarAgent(user_id)
