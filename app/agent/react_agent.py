"""
ReAct-based calendar assistant agent (Chiku).
Uses compassionate, neurodiversity-aware prompting with state management.
"""

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

# State management tools
from app.agent.state_tools import (
    update_working_state,
    update_user_profile,
)

# Calendar query tools (read-only)
from app.agent.calendar_query_tools import (
    get_events,
    get_events_on_date,
    get_todays_schedule,
    get_tomorrows_schedule,
    get_week_schedule,
    find_event_by_title,
)

# Calendar action tools (modify data)
from app.agent.calendar_action_tools import (
    create_calendar_event,
    update_calendar_event,
    move_event_to_date,
    delete_calendar_event,
)

# Availability checking tools
from app.agent.availability_tools import (
    find_available_slots,
    check_time_availability,
)

# Reminder tools
from app.agent.reminder_tools import (
    create_reminder,
    create_reminder_for_event,
    get_upcoming_reminders,
    get_pending_reminders,
    mark_reminder_completed,
    snooze_reminder,
    delete_reminder,
)

# Message tools
from app.agent.message_tools import (
    send_interrogative_message,
    send_declarative_message,
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

        # All available tools organized by category
        self.tools = [
            # State management tools
            update_working_state,
            update_user_profile,
            # Calendar query tools (read-only)
            get_events,
            get_events_on_date,
            get_todays_schedule,
            get_tomorrows_schedule,
            get_week_schedule,
            find_event_by_title,
            # Availability tools
            find_available_slots,
            check_time_availability,
            # Calendar action tools (modify data)
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

        # Get current conversation state (excluding last_tool_calls to avoid duplication)
        state_dict = conversation_service.get_conversation_state_for_prompt(
            self.user_id
        )
        import json

        state_json = json.dumps(state_dict, indent=2)

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

        # CONDITIONAL STATE RESET: Check if last iteration ended with a declarative message
        # If so, reset transient state (but keep user_profile) for fresh conversation
        current_state = conversation_service.get_conversation_state(self.user_id)
        if hasattr(current_state, "last_tool_calls") and current_state.last_tool_calls:
            last_tool = current_state.last_tool_calls[-1]
            last_tool_name = last_tool.get("tool_name", "")

            if last_tool_name == "send_declarative_message":
                logger.info(
                    "Last iteration ended with declarative message - resetting transient state for new conversation"
                )
                conversation_service.reset_transient_state(self.user_id)
                logger.info("✓ Transient state reset, user_profile preserved")

            elif last_tool_name == "send_interrogative_message":
                logger.info(
                    f"Last iteration ended with interrogative message - maintaining context and injecting user response"
                )

                # Update the result of the interrogative message with user's response
                last_tool["result"] = {
                    **last_tool.get("result", {}),
                    "user_response": user_message,
                }

                # Save the updated state
                conversation_service.update_conversation_state(
                    self.user_id, {"last_tool_calls": current_state.last_tool_calls}
                )
                logger.info(
                    f"✓ User response injected into interrogative message result"
                )

        # Save user message to history
        await conversation_service.save_message(self.user_id, "user", user_message)

        # Populate the system prompt with dynamic fields
        system_prompt = await self._populate_prompt()

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

            # Log current state at start of iteration
            current_state = conversation_service.get_conversation_state(self.user_id)
            logger.info("=" * 60)
            logger.info("STATE AT ITERATION START:")
            if hasattr(current_state, "intent"):
                logger.info(f"  Intent: {current_state.intent}")
            if hasattr(current_state, "context"):
                logger.info(f"  Context: {current_state.context}")
            if hasattr(current_state, "planning"):
                logger.info(f"  Planning: {current_state.planning}")
            if hasattr(current_state, "confidence"):
                logger.info(f"  Confidence: {current_state.confidence}")
            if hasattr(current_state, "user_profile") and current_state.user_profile:
                logger.info(
                    f"  User Profile Keys: {list(current_state.user_profile.keys())}"
                )
            logger.info("=" * 60)

            # Calculate tokens needed for this request
            tokens_needed = num_tokens_from_messages(messages, model_name=OPENAI_MODEL)
            tokens_needed += 5000  # Buffer for response

            logger.debug(f"Estimated tokens needed: {tokens_needed}")

            # Retry logic for protocol violations
            max_retries = 2
            retry_count = 0
            response = None

            while retry_count < max_retries:
                # Borrow LLM from pool
                try:
                    slot, lock_token = await llmpool.borrow_llm(tokens_needed)
                    llm_with_tools = slot.llm.bind_tools(self.tools)

                    logger.debug(
                        f"Borrowed LLM slot '{slot.name}' for iteration {iteration}"
                        + (f" (retry {retry_count})" if retry_count > 0 else "")
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

                    # Check for protocol violations
                    if not response.tool_calls:
                        logger.error("=" * 80)
                        logger.error(f"PROTOCOL VIOLATION [RED] - NO TOOL CALLS")
                        logger.error(f"Retry: {retry_count + 1}/{max_retries}")
                        logger.error("-" * 80)
                        logger.error(f"Response type: {type(response)}")
                        logger.error(
                            f"Response content: {response.content if hasattr(response, 'content') else 'N/A'}"
                        )
                        logger.error(
                            f"Has tool_calls attr: {hasattr(response, 'tool_calls')}"
                        )
                        logger.error(f"Tool calls value: {response.tool_calls}")
                        logger.error("-" * 80)
                        logger.error("MESSAGES SENT TO LLM:")
                        for idx, msg in enumerate(messages):
                            msg_type = type(msg).__name__
                            msg_preview = (
                                str(msg.content)[:200]
                                if hasattr(msg, "content")
                                else str(msg)[:200]
                            )
                            logger.error(f"  [{idx}] {msg_type}: {msg_preview}...")
                        logger.error("=" * 80)
                        retry_count += 1
                        if retry_count < max_retries:
                            # Add a system message to guide the retry
                            messages.append(
                                SystemMessage(
                                    content="ERROR: You must call tools. You cannot respond with plain text. "
                                    "Call update_working_state first, then at least one other tool."
                                )
                            )
                            continue
                        else:
                            # Final retry failed - force a message tool
                            logger.error(
                                "All retries exhausted - forcing fallback response"
                            )
                            final_response = "I apologize, I'm having trouble processing your request right now. Could you please rephrase?"
                            await conversation_service.save_message(
                                self.user_id, "assistant", final_response
                            )
                            return final_response

                    elif len(response.tool_calls) < 2:
                        tool_names = [tc["name"] for tc in response.tool_calls]
                        logger.error("=" * 80)
                        logger.error(
                            f"PROTOCOL VIOLATION [YELLOW] - INSUFFICIENT TOOL CALLS"
                        )
                        logger.error(f"Retry: {retry_count + 1}/{max_retries}")
                        logger.error("-" * 80)
                        logger.error(f"Expected: Minimum 2 tool calls")
                        logger.error(f"Actual: {len(response.tool_calls)} tool call(s)")
                        logger.error(f"Tools called: {tool_names}")
                        logger.error("-" * 80)
                        logger.error("DETAILED TOOL CALL INFORMATION:")
                        for idx, tc in enumerate(response.tool_calls):
                            logger.error(f"  Tool Call {idx + 1}:")
                            logger.error(f"    Name: {tc['name']}")
                            logger.error(f"    ID: {tc.get('id', 'N/A')}")
                            logger.error(f"    Arguments: {tc.get('args', {})}")
                        logger.error("-" * 80)
                        logger.error("VIOLATION ANALYSIS:")
                        has_state_update = "update_working_state" in tool_names
                        has_message_tool = (
                            "send_interrogative_message" in tool_names
                            or "send_declarative_message" in tool_names
                        )
                        has_query_tool = any(
                            tn
                            in [
                                "get_events",
                                "get_events_on_date",
                                "get_todays_schedule",
                                "get_tomorrows_schedule",
                                "get_week_schedule",
                                "find_event_by_title",
                                "find_available_slots",
                                "check_time_availability",
                                "get_upcoming_reminders",
                                "get_pending_reminders",
                            ]
                            for tn in tool_names
                        )
                        has_action_tool = any(
                            tn
                            in [
                                "create_calendar_event",
                                "update_calendar_event",
                                "move_event_to_date",
                                "delete_calendar_event",
                                "create_reminder",
                                "create_reminder_for_event",
                                "mark_reminder_completed",
                                "snooze_reminder",
                                "delete_reminder",
                            ]
                            for tn in tool_names
                        )

                        logger.error(
                            f"  {'✓' if has_state_update else '✗'} Has update_working_state: {has_state_update}"
                        )
                        logger.error(
                            f"  {'✓' if has_message_tool else '✗'} Has message tool: {has_message_tool}"
                        )
                        logger.error(
                            f"  {'✓' if has_query_tool else '✗'} Has query tool: {has_query_tool}"
                        )
                        logger.error(
                            f"  {'✓' if has_action_tool else '✗'} Has action tool: {has_action_tool}"
                        )
                        logger.error("-" * 80)
                        logger.error("WHAT'S MISSING:")
                        if not has_state_update:
                            logger.error(
                                "  ⚠️  CRITICAL: update_working_state must be called (even if just refining reasoning)"
                            )
                        if not (has_message_tool or has_query_tool or has_action_tool):
                            logger.error(
                                "  ⚠️  CRITICAL: Need at least one action (message/query/management tool)"
                            )
                            if has_state_update:
                                logger.error(
                                    "  💡 HINT: Did you write a plan in state.next_microstep but forget to EXECUTE it?"
                                )
                                logger.error(
                                    "         State is PLANNING, actions are EXECUTING. Both required!"
                                )
                        logger.error("-" * 80)
                        logger.error("MESSAGES SENT TO LLM:")
                        for idx, msg in enumerate(messages):
                            msg_type = type(msg).__name__
                            msg_preview = (
                                str(msg.content)[:200]
                                if hasattr(msg, "content")
                                else str(msg)[:200]
                            )
                            logger.error(f"  [{idx}] {msg_type}: {msg_preview}...")
                        logger.error("=" * 80)
                        retry_count += 1
                        if retry_count < max_retries:
                            # Add a system message to guide the retry
                            retry_guidance = (
                                "ERROR: You must call at least 2 tools per iteration: "
                                "1) update_working_state and "
                                "2) At least one action tool (query, calendar action, or message tool). "
                            )

                            # Add specific hint if only state update was called
                            if (
                                len(response.tool_calls) == 1
                                and response.tool_calls[0]["name"]
                                == "update_working_state"
                            ):
                                retry_guidance += (
                                    "CRITICAL HINT: You called update_working_state but forgot the action! "
                                    "If your state says 'next_microstep: ask user...', you must ALSO call send_interrogative_message in the SAME iteration. "
                                    "State is PLANNING what you'll do. Actions are EXECUTING the plan. Both required together!"
                                )

                            messages.append(SystemMessage(content=retry_guidance))
                            continue
                        else:
                            # Final retry failed - let it proceed but log
                            logger.error(
                                "All retries exhausted - proceeding with insufficient tool calls"
                            )
                            logger.error(f"Final tool calls: {tool_names}")
                            break
                    else:
                        # Valid response - break out of retry loop
                        break

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

            # If we got here without a valid response, something went wrong
            if not response or not response.tool_calls:
                logger.error("Failed to get valid response after retries")
                final_response = "I apologize, I'm having trouble processing your request. Please try again."
                await conversation_service.save_message(
                    self.user_id, "assistant", final_response
                )
                return final_response

            messages.append(response)

            # Tool calls are guaranteed valid at this point (passed retry logic)

            logger.info(f"Tool calls requested: {len(response.tool_calls)}")

            # Track tool calls for next iteration's prompt
            tool_calls_record = []

            # Validate that update_working_state was called (regardless of position)
            tool_names_called = [tc["name"] for tc in response.tool_calls]
            state_update_found = "update_working_state" in tool_names_called

            if not state_update_found:
                logger.warning("=" * 80)
                logger.warning("PROTOCOL RECOMMENDATION VIOLATION - NO STATE UPDATE")
                logger.warning("-" * 80)
                logger.warning(f"Expected: update_working_state should be called")
                logger.warning(f"Actual: update_working_state NOT called")
                logger.warning(f"Tools called instead: {tool_names_called}")
                logger.warning("-" * 80)
                logger.warning("DETAILED TOOL CALL INFORMATION:")
                for idx, tc in enumerate(response.tool_calls):
                    logger.warning(f"  Tool Call {idx + 1}:")
                    logger.warning(f"    Name: {tc['name']}")
                    logger.warning(f"    Arguments: {tc.get('args', {})}")
                logger.warning("-" * 80)
                logger.warning("IMPACT: Poor context tracking across iterations")
                logger.warning("=" * 80)

            # Prepare all tool call coroutines for parallel execution
            tool_coroutines = []
            tool_metadata = []  # Track metadata for each coroutine

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                logger.info(f"\nPreparing tool: {tool_name}")
                logger.info(f"Arguments: {tool_args}")

                # Inject user_id for all tools that need it (all except message tools)
                if tool_name not in [
                    "send_interrogative_message",
                    "send_declarative_message",
                ]:
                    if "user_id" not in tool_args:
                        tool_args["user_id"] = self.user_id

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

                # Log detailed state updates when update_working_state is called
                if tool_name == "update_working_state":
                    state_dict = tool_args.get("state_dict", {})
                    logger.info("=" * 60)
                    logger.info("LLM REQUESTED STATE UPDATE:")
                    if "intent" in state_dict:
                        logger.info(f"  Intent:")
                        for key, val in state_dict["intent"].items():
                            logger.info(f"    - {key}: {val}")
                    if "reasoning" in state_dict:
                        reasoning = state_dict["reasoning"]
                        logger.info(
                            f"  Reasoning: {reasoning[:200]}{'...' if len(reasoning) > 200 else ''}"
                        )
                    if "context" in state_dict:
                        logger.info(f"  Context: {state_dict['context']}")
                    if "planning" in state_dict:
                        logger.info(f"  Planning: {state_dict['planning']}")
                    if "confidence" in state_dict:
                        logger.info(f"  Confidence: {state_dict['confidence']}")
                    # Log any custom fields
                    custom_fields = {
                        k: v
                        for k, v in state_dict.items()
                        if k
                        not in [
                            "intent",
                            "reasoning",
                            "context",
                            "planning",
                            "confidence",
                        ]
                    }
                    if custom_fields:
                        logger.info(f"  Custom Fields: {list(custom_fields.keys())}")
                    logger.info("=" * 60)

                # Log user profile updates
                if tool_name == "update_user_profile":
                    profile_updates = tool_args.get("profile_updates", {})
                    logger.info("=" * 60)
                    logger.info("LLM REQUESTED PROFILE UPDATE:")
                    for category, updates in profile_updates.items():
                        logger.info(f"  {category}: {updates}")
                    logger.info("=" * 60)

                # Track this tool call for next iteration
                tool_calls_record.append(
                    {"tool_name": tool_name, "args": tool_args, "result": tool_result}
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

        # Safety fallback if we hit max iterations
        if final_response is None:
            logger.warning(f"Hit max iterations ({max_iterations})")
            final_response = "I apologize, but I'm having trouble processing your request. Could you please rephrase?"
            await conversation_service.save_message(
                self.user_id, "assistant", final_response
            )

        logger.info("=" * 80)
        return final_response

    async def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> Any:
        """Execute a tool by name with given arguments."""
        tool_map = {
            # State management tools
            "update_working_state": update_working_state,
            "update_user_profile": update_user_profile,
            # Calendar query tools (read-only)
            "get_events": get_events,
            "get_events_on_date": get_events_on_date,
            "get_todays_schedule": get_todays_schedule,
            "get_tomorrows_schedule": get_tomorrows_schedule,
            "get_week_schedule": get_week_schedule,
            "find_event_by_title": find_event_by_title,
            # Availability tools
            "find_available_slots": find_available_slots,
            "check_time_availability": check_time_availability,
            # Calendar action tools (modify data)
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
