"""
ReAct-based calendar assistant agent (Chiku).
Uses compassionate, neurodiversity-aware prompting with state management.
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

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
from app.agent.message_tools import (
    send_interrogative_message,
    send_declarative_message,
)
from app.services.conversation_service import conversation_service
from app.config import OPENAI_API_KEY, OPENAI_MODEL

# Configure logging
logger = logging.getLogger(__name__)


class ReactCalendarAgent:
    """
    ReAct-based autonomous agent with emotional intelligence and state management.
    Implements the Chiku persona for ADHD-aware executive function support.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0.7)

        # All available tools
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
            # Message tools
            send_interrogative_message,
            send_declarative_message,
        ]
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Load the mega prompt
        self.system_prompt_template = self._load_mega_prompt()

        # Callback for sending messages to user (set by websocket handler)
        self.message_callback: Optional[Callable[[str], None]] = None

        logger.info(f"Initialized ReAct agent for user: {user_id}")

    def _load_mega_prompt(self) -> str:
        """Load the mega prompt template from file."""
        try:
            with open("app/agent/mega_prompt.txt", "r") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load mega_prompt.txt: {e}")
            # Fallback basic prompt
            return "You are Chiku, a helpful calendar assistant."

    async def _populate_prompt(self, user_message: str) -> str:
        """
        Populate the dynamic fields in the mega prompt.

        Dynamic fields:
        - {{Last 5 messages}}
        - {{last_state_json}}
        - {{last_partial_update}}
        - {{last_tool_action_and_result}}
        """
        # Get recent messages
        recent_messages = await conversation_service.format_recent_messages(
            self.user_id, limit=5
        )

        # Get current conversation state
        current_state = conversation_service.get_conversation_state(self.user_id)
        state_json = current_state.model_dump_json(indent=2)

        # Get last partial update (from current state's reasoning)
        last_partial_update = (
            f"reasoning: {current_state.reasoning}"
            if current_state.reasoning
            else "No previous update"
        )

        # Last tool action and result (stored in messages - get last assistant message)
        messages = await conversation_service.get_recent_messages(self.user_id, limit=3)
        last_tool_info = "No previous tool call"
        for msg in reversed(messages):
            if msg.role == "assistant" and "tool" in msg.content.lower():
                last_tool_info = msg.content
                break

        # Populate the template
        prompt = self.system_prompt_template
        prompt = prompt.replace("{{Last 5 messages}}", recent_messages)
        prompt = prompt.replace("{{last_state_json}}", state_json)
        prompt = prompt.replace("{{last_partial_update}}", last_partial_update)
        prompt = prompt.replace("{{last_tool_action_and_result}}", last_tool_info)

        # Add current date
        current_date = datetime.now().strftime("%Y-%m-%d")
        prompt = f"{prompt}\n\nCurrent date: {current_date}"

        return prompt

    def set_message_callback(self, callback: Callable[[str], None]):
        """Set callback function for sending messages to user via WebSocket."""
        self.message_callback = callback

    async def chat(self, user_message: str) -> str:
        """
        Process a user message using the ReAct loop.

        Returns the final message to send to the user.
        """
        logger.info("=" * 80)
        logger.info(f"USER: {user_message}")

        # Save user message to history
        await conversation_service.save_message(self.user_id, "user", user_message)

        # Populate the system prompt with dynamic fields
        system_prompt = await self._populate_prompt(user_message)

        # Initialize conversation with system prompt and user message
        messages: List[Any] = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]

        # ReAct loop - iterate until a message tool is called
        max_iterations = 10
        iteration = 0
        final_response = None

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"\n--- Iteration {iteration} ---")

            # Call LLM with tools
            response = self.llm_with_tools.invoke(messages)
            messages.append(response)

            # Check if LLM called any tools
            if not response.tool_calls:
                # No tools called - LLM provided reasoning/response directly
                content = str(response.content) if response.content else ""
                logger.info(f"LLM responded without tool call. Raw content: {content}")

                # Try to parse JSON and extract message if it's structured output
                try:
                    import json

                    parsed = json.loads(content)

                    # Look for the actual message in various possible locations
                    if isinstance(parsed, dict):
                        # Check if there's a next_action_request with tool_args.content
                        if (
                            "next_action_request" in parsed
                            and "tool_args" in parsed["next_action_request"]
                        ):
                            final_response = parsed["next_action_request"][
                                "tool_args"
                            ].get("content", content)
                        # Check if there's direct content field
                        elif "content" in parsed:
                            final_response = parsed["content"]
                        else:
                            final_response = content
                    else:
                        final_response = content

                    logger.info(f"Extracted message: {final_response}")
                except (json.JSONDecodeError, KeyError, TypeError):
                    # Not JSON or unexpected structure, use as-is
                    final_response = content

                break

            # Execute tool calls
            logger.info(f"Tool calls requested: {len(response.tool_calls)}")

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                logger.info(f"\nCalling tool: {tool_name}")
                logger.info(f"Arguments: {tool_args}")

                # Inject user_id for all non-message tools if not present
                if tool_name not in [
                    "send_interrogative_message",
                    "send_declarative_message",
                ]:
                    if "user_id" not in tool_args:
                        tool_args["user_id"] = self.user_id

                # Execute the tool
                tool_result = await self._execute_tool(tool_name, tool_args)
                logger.info(f"Tool result: {tool_result}")

                # Extract and update conversation state from partial_state_update
                if (
                    isinstance(tool_result, dict)
                    and "partial_state_update" in tool_result
                ):
                    partial_update = tool_result["partial_state_update"]
                    if partial_update:
                        conversation_service.update_conversation_state(
                            self.user_id, partial_update
                        )
                        logger.info(
                            f"Updated conversation state with: {partial_update}"
                        )

                # Add tool result to messages
                messages.append(
                    ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call["id"],
                    )
                )

                # Check if this is a message tool (end of iteration)
                if isinstance(tool_result, dict) and tool_result.get("stop_iteration"):
                    final_response = tool_result.get("content", "")
                    logger.info(f"Message tool called, ending iteration")
                    logger.info(f"CHIKU: {final_response}")

                    # Send message via callback if available
                    if self.message_callback:
                        self.message_callback(final_response)

                    # Save assistant message to history
                    await conversation_service.save_message(
                        self.user_id, "assistant", final_response
                    )

                    logger.info("=" * 80)
                    return final_response

        # Safety fallback if we hit max iterations
        if final_response is None:
            logger.warning(f"Hit max iterations ({max_iterations})")
            final_response = "I apologize, but I'm having trouble processing your request. Could you please rephrase?"

            # Save fallback message
            await conversation_service.save_message(
                self.user_id, "assistant", final_response
            )

        logger.info("=" * 80)
        return final_response

    async def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
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
            # Message tools
            "send_interrogative_message": send_interrogative_message,
            "send_declarative_message": send_declarative_message,
        }

        tool = tool_map.get(tool_name)
        if not tool:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            result = await tool.ainvoke(tool_args)
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return {"error": str(e)}

    def reset_conversation(self):
        """Reset the conversation state and history."""
        conversation_service.reset_conversation_state(self.user_id)
        logger.info("Conversation state reset")


def create_react_agent(user_id: str) -> ReactCalendarAgent:
    """Factory function to create a ReAct agent."""
    return ReactCalendarAgent(user_id)
