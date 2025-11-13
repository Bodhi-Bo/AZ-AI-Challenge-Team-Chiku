"""
ReAct-based calendar assistant agent (Chiku).
Uses compassionate, neurodiversity-aware prompting with state management.
"""

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from app.agent.mongo_tools import (
    get_events,
    get_events_on_date,
    get_todays_schedule,
    get_tomorrows_schedule,
    get_week_schedule,
    find_event_by_title,
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
from app.agent.state_tools import (
    update_working_state,
)
from app.agent.tool_context import (
    set_current_user_id,
    reset_current_user_id,
)
from app.services.conversation_service import conversation_service
from app.services.openai_llmpool_service import llmpool
from app.utils.token_util import num_tokens_from_messages
from app.config import OPENAI_MODEL

# Configure logging
logger = logging.getLogger(__name__)


class ReactCalendarAgent:
    """
    ReAct-based autonomous agent with emotional intelligence and state management.
    Implements the Chiku persona for ADHD-aware executive function support.
    Uses the LLM pool to borrow/return LLM instances efficiently.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        # We no longer create our own LLM - we'll borrow from the pool

        # All available tools (now including update_working_state)
        self.tools = [
            # State management (MUST be called first)
            update_working_state,
            # Calendar query tools
            get_events,
            get_events_on_date,
            get_todays_schedule,
            get_tomorrows_schedule,
            get_week_schedule,
            find_event_by_title,
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

    async def _populate_prompt(self) -> str:
        """
        Populate the dynamic fields in the mega prompt.

        Dynamic fields:
        - {{Last 5 messages}}
        - {{last_state_json}}
        - {{last_tool_actions_and_result}}
        """
        # Get recent messages
        recent_messages = await conversation_service.format_recent_messages(
            self.user_id, limit=5
        )

        # Get current conversation state
        current_state = conversation_service.get_conversation_state(self.user_id)
        state_json = current_state.model_dump_json(indent=2)

        # Format last tool actions and results from conversation state
        # This includes all tools called in the last iteration
        last_tool_info = self._format_last_tool_calls()

        # Populate the template
        prompt = self.system_prompt_template
        prompt = prompt.replace("{{Last 5 messages}}", recent_messages)
        prompt = prompt.replace("{{last_state_json}}", state_json)
        prompt = prompt.replace("{{last_tool_actions_and_result}}", last_tool_info)

        # Add current date
        current_date = datetime.now().strftime("%Y-%m-%d")
        prompt = f"{prompt}\n\nCurrent date: {current_date}"

        return prompt

    def _format_last_tool_calls(self) -> str:
        """
        Format the last iteration's tool calls and results for the prompt.
        Retrieves this information from the conversation state.
        """
        current_state = conversation_service.get_conversation_state(self.user_id)

        # Check if we have tracked tool calls in the state
        if hasattr(current_state, "last_tool_calls") and current_state.last_tool_calls:
            tool_calls_summary = []
            for call in current_state.last_tool_calls:
                tool_name = call.get("tool_name", "unknown")
                result = call.get("result", {})
                tool_calls_summary.append(f"Tool: {tool_name}\nResult: {result}\n")
            return "\n".join(tool_calls_summary)

        return "No previous tool calls"

    def set_message_callback(self, callback: Callable[[str], None]):
        """Set callback function for sending messages to user via WebSocket."""
        self.message_callback = callback

    async def chat(self, user_message: str) -> str:
        """
        Process a user message using the ReAct loop with new architecture:
        - Enforces update_working_state as first tool call
        - Supports multiple tool calls per iteration (up to 7)
        - Validates minimum 2 calls per iteration
        - Extracts and stores state separately
        - Executes all tools in parallel using asyncio.gather()
        - Injects user response as the result of the previous message tool

        Returns the final message to send to the user.
        """
        logger.info("=" * 80)
        logger.info(f"USER: {user_message}")

        # INJECT USER RESPONSE: Check if the last iteration ended with a message tool
        # If so, update that tool call's result with the current user_message
        current_state = conversation_service.get_conversation_state(self.user_id)
        if hasattr(current_state, "last_tool_calls") and current_state.last_tool_calls:
            last_tool = current_state.last_tool_calls[-1]
            last_tool_name = last_tool.get("tool_name", "")

            if last_tool_name in [
                "send_interrogative_message",
                "send_declarative_message",
            ]:
                logger.info(
                    f"Last iteration ended with {last_tool_name}, injecting user response into result"
                )

                # Update the result of the last message tool with user's response
                last_tool["result"] = {
                    **last_tool.get("result", {}),
                    "user_response": user_message,
                }

                # Save the updated state
                conversation_service.update_conversation_state(
                    self.user_id, {"last_tool_calls": current_state.last_tool_calls}
                )
                logger.info(f"✓ User response injected into {last_tool_name} result")

        # Save user message to history
        await conversation_service.save_message(self.user_id, "user", user_message)

        # Populate the system prompt with dynamic fields
        system_prompt = await self._populate_prompt()

        # Initialize conversation with system prompt and user message
        messages: List[Any] = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]

        # Set the user_id context for all tool executions
        context_token = set_current_user_id(self.user_id)

        try:
            # ReAct loop - iterate until a message tool is called
            max_iterations = 10
            iteration = 0
            final_response = None

            while iteration < max_iterations:
                iteration += 1
                logger.info(f"\n--- Iteration {iteration} ---")

                # Calculate tokens needed for this request
                tokens_needed = num_tokens_from_messages(
                    messages, model_name=OPENAI_MODEL
                )
                tokens_needed += 5000  # Buffer for response

                logger.debug(f"Estimated tokens needed: {tokens_needed}")

                # Borrow LLM from pool
                try:
                    slot, lock_token = await llmpool.borrow_llm(tokens_needed)
                    llm_with_tools = slot.llm.bind_tools(self.tools)

                    logger.debug(
                        f"Borrowed LLM slot '{slot.name}' for iteration {iteration}"
                    )

                    # Call LLM with tools
                    response = llm_with_tools.invoke(messages)

                    # Extract actual token usage
                    actual_tokens = tokens_needed
                    if hasattr(response, "response_metadata"):
                        usage = response.response_metadata.get("token_usage", {})
                        if usage:
                            actual_tokens = usage.get("prompt_tokens", 0) + usage.get(
                                "completion_tokens", 0
                            )
                            logger.debug(f"Actual tokens used: {actual_tokens}")

                    # Record usage and return the slot
                    llmpool.record_slot_usage(slot, actual_tokens)
                    llmpool.return_llm(slot, lock_token)

                except ValueError as e:
                    logger.error(f"Error using LLM slot: {e}")
                    final_response = "I'm experiencing high demand right now. Please try again in a moment."
                    await conversation_service.save_message(
                        self.user_id, "assistant", final_response
                    )
                    return final_response
                except Exception as e:
                    logger.error(f"Unexpected error in chat: {e}", exc_info=True)
                    final_response = (
                        "I apologize, but I encountered an error. Please try again."
                    )
                    await conversation_service.save_message(
                        self.user_id, "assistant", final_response
                    )
                    return final_response

                messages.append(response)

                # Check if LLM called any tools
                if not response.tool_calls:
                    # No tools called - LLM provided reasoning/response directly (ERROR STATE)
                    content = str(response.content) if response.content else ""
                    logger.warning(
                        f"LLM responded without tool calls. This violates the protocol. Content: {content}"
                    )

                    # Force it to call at least the message tool
                    final_response = (
                        content or "I apologize, I need to reconsider my approach."
                    )
                    await conversation_service.save_message(
                        self.user_id, "assistant", final_response
                    )
                    break

                # VALIDATION: Check minimum 2 tool calls (state + action)
                if len(response.tool_calls) < 2:
                    logger.error(
                        f"Protocol violation: Only {len(response.tool_calls)} tool call(s). Minimum is 2 (state + action)"
                    )
                    # Let it proceed but log the violation - the LLM might self-correct next iteration

                # VALIDATION: Check that first tool call is update_working_state
                first_tool_name = response.tool_calls[0]["name"]
                if first_tool_name != "update_working_state":
                    logger.error(
                        f"Protocol violation: First tool call must be update_working_state, got {first_tool_name}"
                    )
                    # Continue anyway - might self-correct

                logger.info(f"Tool calls requested: {len(response.tool_calls)}")

                # Track tool calls for next iteration's prompt
                tool_calls_record = []
                state_update_found = False

                # Prepare all tool call coroutines for parallel execution
                tool_coroutines = []
                tool_metadata = []  # Track metadata for each coroutine

                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]

                    logger.info(f"\nPreparing tool: {tool_name}")
                    logger.info(f"Arguments: {tool_args}")

                    # Create coroutine for this tool
                    tool_coroutines.append(self._execute_tool(tool_name, tool_args))
                    tool_metadata.append(
                        {
                            "tool_name": tool_name,
                            "tool_args": tool_args,
                            "tool_call_id": tool_call["id"],
                        }
                    )

                # Execute ALL tools in parallel
                logger.info(
                    f"Executing {len(tool_coroutines)} tools in parallel using asyncio.gather..."
                )
                tool_results = await asyncio.gather(*tool_coroutines)

                # Process results
                for i, tool_result in enumerate(tool_results):
                    meta = tool_metadata[i]
                    tool_name = meta["tool_name"]
                    tool_args = meta["tool_args"]
                    tool_call_id = meta["tool_call_id"]

                    logger.info(f"\n✓ Tool completed: {tool_name}")
                    logger.info(f"Result: {tool_result}")

                    # Track this tool call for next iteration
                    tool_calls_record.append(
                        {
                            "tool_name": tool_name,
                            "args": tool_args,
                            "result": tool_result,
                        }
                    )

                    # Handle state update tool specially
                    if tool_name == "update_working_state":
                        state_update_found = True
                        if isinstance(tool_result, dict) and tool_result.get("success"):
                            state_dict = tool_result.get("state_dict", {})
                            if state_dict:
                                # Update conversation state with the new state
                                conversation_service.update_conversation_state(
                                    self.user_id, state_dict
                                )
                                logger.info(
                                    f"✓ Conversation state updated from update_working_state tool"
                                )

                    # Add tool result to messages
                    messages.append(
                        ToolMessage(
                            content=str(tool_result),
                            tool_call_id=tool_call_id,
                        )
                    )

                    # Check if this is a message tool (end of iteration)
                    if isinstance(tool_result, dict) and "message_type" in tool_result:
                        final_response = tool_result.get("content", "")
                        logger.info(f"Message tool detected: {tool_name}")
                        logger.info(f"CHIKU: {final_response}")

                        # Save tool calls record to state for next iteration
                        conversation_service.update_conversation_state(
                            self.user_id, {"last_tool_calls": tool_calls_record}
                        )

                        # Send message via callback if available
                        if self.message_callback:
                            self.message_callback(final_response)

                        # Save assistant message to history
                        await conversation_service.save_message(
                            self.user_id, "assistant", final_response
                        )

                        logger.info("=" * 80)
                        return final_response

                # Save tool calls record for next iteration even if no message tool was called
                conversation_service.update_conversation_state(
                    self.user_id, {"last_tool_calls": tool_calls_record}
                )

                if not state_update_found:
                    logger.warning(
                        "No update_working_state call found in this iteration"
                    )

            # Safety fallback if we hit max iterations
            if final_response is None:
                logger.warning(f"Hit max iterations ({max_iterations})")
                final_response = "I apologize, but I'm having trouble processing your request. Could you please rephrase?"
                await conversation_service.save_message(
                    self.user_id, "assistant", final_response
                )

            logger.info("=" * 80)
            return final_response

        finally:
            # Always reset the user_id context when done
            reset_current_user_id(context_token)

    async def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """Execute a tool by name with given arguments."""
        tool_map = {
            # State management
            "update_working_state": update_working_state,
            # Calendar query tools
            "get_events": get_events,
            "get_events_on_date": get_events_on_date,
            "get_todays_schedule": get_todays_schedule,
            "get_tomorrows_schedule": get_tomorrows_schedule,
            "get_week_schedule": get_week_schedule,
            "find_event_by_title": find_event_by_title,
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
