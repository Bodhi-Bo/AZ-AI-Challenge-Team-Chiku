"""
ReAct-based calendar assistant agent (Chiku).
Uses compassionate, neurodiversity-aware prompting with state management.
"""

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
import logging
import asyncio
import json
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from app.agent_tools.mongo_tools import (
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
from app.agent_tools.message_tools import (
    send_interrogative_message,
    send_declarative_message,
)
from app.agent_tools.state_tools import (
    update_working_state,
    reset_conversation_state,
)
from app.agent_tools.decomposer_tools import (
    talk_to_decomposer_agent,
)
from app.agent_tools.tool_context import (
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

        # All available tools (now including update_working_state and talk_to_decomposer_agent)
        self.tools = [
            # State management (MANDATORY)
            update_working_state,
            reset_conversation_state,
            # Task decomposition
            talk_to_decomposer_agent,
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
            with open("app/agents/react/mega_prompt.txt", "r") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load mega_prompt.txt: {e}")
            raise RuntimeError("Mega prompt file is missing.")

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

    def _inject_user_response_into_last_message_tool(self, user_message: str) -> None:
        """
        Inject user response as the result of the previous message tool call.

        If the last iteration ended with a message tool (interrogative or declarative),
        this updates that tool's result with the current user_message.
        """
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

    def _validate_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> None:
        """
        Validate tool calls against protocol requirements.

        Logs warnings/errors for violations:
        - Minimum 2 tool calls (state + action)
        - First tool call should be update_working_state
        """
        # Check minimum 2 tool calls (state + action)
        if len(tool_calls) < 2:
            logger.error(
                f"Protocol violation: Only {len(tool_calls)} tool call(s). Minimum is 2 (state + action)"
            )

        # Check that first tool call is update_working_state
        first_tool_name = tool_calls[0]["name"]
        if first_tool_name != "update_working_state":
            logger.error(
                f"Protocol violation: First tool call should be update_working_state, got {first_tool_name}"
            )

    async def _borrow_llm_and_invoke(
        self, messages: List[Any], iteration: int
    ) -> Optional[Any]:
        """
        Borrow an LLM from the pool, invoke it with messages, and return it.

        Returns the LLM response or None if an error occurred.
        """
        # Calculate tokens needed for this request
        tokens_needed = num_tokens_from_messages(messages, model_name=OPENAI_MODEL)
        tokens_needed += 5000  # Buffer for response

        logger.debug(f"Estimated tokens needed: {tokens_needed}")

        try:
            # Borrow LLM from pool
            slot, lock_token = await llmpool.borrow_llm(tokens_needed)
            llm_with_tools = slot.llm.bind_tools(self.tools)

            logger.debug(f"Borrowed LLM slot '{slot.name}' for iteration {iteration}")

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

            return response

        except ValueError as e:
            logger.error(f"Error using LLM slot: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error invoking LLM: {e}", exc_info=True)
            return None

    async def _execute_tools_in_parallel(
        self, tool_calls: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], List[ToolMessage]]:
        """
        Execute all tool calls in parallel and return results.

        Returns:
            tuple: (tool_calls_record, tool_messages)
                - tool_calls_record: List of dicts tracking tool calls for next iteration
                - tool_messages: List of ToolMessage objects to append to conversation
        """
        logger.info(f"Tool calls requested: {len(tool_calls)}")

        tool_calls_record = []

        # Prepare all tool call coroutines for parallel execution
        tool_coroutines = []
        tool_metadata = []

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            logger.info(f"\nPreparing tool: {tool_name}")
            logger.info(f"Arguments: {tool_args}")

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
        tool_messages = []
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
                if isinstance(tool_result, dict) and tool_result.get("success"):
                    state_dict = tool_result.get("state_dict", {})
                    if state_dict:
                        conversation_service.update_conversation_state(
                            self.user_id, state_dict
                        )
                        logger.info(
                            f"✓ Conversation state updated from update_working_state tool"
                        )

            # Add tool result to messages
            tool_messages.append(
                ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call_id,
                )
            )

        return tool_calls_record, tool_messages

    def _check_for_message_tool_result(
        self, tool_calls_record: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Check if any tool call was a message tool and return its content.
        Also handles batch questions from decomposer.

        Returns the message content if found, None otherwise.
        """
        for tool_call in tool_calls_record:
            tool_name = tool_call["tool_name"]
            tool_result = tool_call["result"]

            # Handle regular message tools
            if isinstance(tool_result, dict) and "message_type" in tool_result:
                message_content = tool_result.get("content", "")
                logger.info(f"Message tool detected: {tool_name}")
                logger.info(f"CHIKU: {message_content}")
                return message_content

            # Handle batch questions from decomposer
            if (
                isinstance(tool_result, dict)
                and tool_result.get("awaiting_responses") is True
            ):
                logger.info(
                    "Batch questions detected from decomposer - entering collection mode"
                )
                return self._handle_batch_questions_sync(tool_result)

        return None

    def _handle_batch_questions_sync(self, batch_result: Dict[str, Any]) -> str:
        """
        Handle batch questions by storing them in state and returning the first question.
        The conversation will continue across multiple user messages to collect all answers.

        This is a synchronous method that prepares the batch question state.
        The actual question-answer collection happens across multiple chat() calls.
        """
        questions = batch_result.get("questions", [])

        if not questions:
            return "I need some clarification, but something went wrong. Could you provide more details?"

        # Store batch questions in conversation state under 'decomposer' field
        decomposer_state = {
            "batch_questions": questions,
            "batch_answers": [],
            "current_question_index": 0,
        }

        conversation_service.update_conversation_state(
            self.user_id,
            {"batch_questions_active": True, "decomposer": decomposer_state},
        )

        # Return the first question
        first_q = questions[0]
        question_text = first_q.get("question", "")
        hint = first_q.get("hint", "")

        message = question_text
        if hint:
            message += f"\n\n{hint}"

        logger.info(f"CHIKU (batch Q1/{len(questions)}): {message}")
        return message

    async def _continue_batch_question_collection(self, user_answer: str) -> str | None:
        """
        Continue collecting answers for batch questions in a natural, conversational way.

        This method simply collects the user's natural language answer without rigid validation.
        The decomposer agent will interpret the answers intelligently when creating the plan.

        Returns the next question, or None if all questions are answered (signaling to continue to normal ReAct loop).
        """
        current_state = conversation_service.get_conversation_state(self.user_id)

        # Get decomposer state
        decomposer = getattr(current_state, "decomposer", {})
        questions = decomposer.get("batch_questions", [])
        answers = decomposer.get("batch_answers", [])
        current_index = decomposer.get("current_question_index", 0)

        if current_index >= len(questions):
            logger.error("Batch question index out of range - resetting")
            conversation_service.update_conversation_state(
                self.user_id, {"batch_questions_active": False, "decomposer": {}}
            )
            return "Sorry, something went wrong with the questions. Let's start over."

        current_q = questions[current_index]
        question_text = current_q.get("question", "")

        # Store the answer as-is (no validation - let decomposer interpret)
        logger.info(
            f"✓ Answer {current_index + 1}/{len(questions)} collected: {user_answer[:50]}..."
        )
        answers.append({"question": question_text, "answer": user_answer})

        # Move to next question or complete
        next_index = current_index + 1

        if next_index >= len(questions):
            # All questions answered - complete batch collection
            logger.info(
                f"✓ All {len(questions)} questions answered - completing batch collection"
            )

            # Keep decomposer state with all collected answers (don't clear!)
            # The answers will be passed to decomposer on next call
            decomposer["batch_answers"] = answers
            decomposer["current_question_index"] = None  # Mark as complete

            # Save the last answer to message history
            await conversation_service.save_message(self.user_id, "user", user_answer)

            # Exit batch mode BEFORE continuing to normal loop
            conversation_service.update_conversation_state(
                self.user_id,
                {
                    "batch_questions_active": False,  # Exit batch mode
                    "decomposer": decomposer,  # Persist state with answers
                },
            )

            # Log that we're transitioning to normal mode
            logger.info(
                "🔄 Exiting batch mode - continuing to normal ReAct loop with all answers collected"
            )

            # Return None to signal we should continue to normal processing
            # The caller will check for this and fall through to the normal loop
            return None

        # More questions remaining - ask next one
        decomposer["batch_answers"] = answers
        decomposer["current_question_index"] = next_index

        conversation_service.update_conversation_state(
            self.user_id,
            {
                "decomposer": decomposer,
            },
        )

        next_q = questions[next_index]
        next_question_text = next_q.get("question", "")
        next_hint = next_q.get("hint", "")

        message = f"Thanks! ({next_index + 1}/{len(questions)})\n\n{next_question_text}"
        if next_hint:
            message += f"\n\n{next_hint}"

        logger.info(f"CHIKU (batch Q{next_index + 1}/{len(questions)}): {message}")
        return message

    async def chat(self, user_message: str) -> str:
        """
        Process a user message using the ReAct loop with new architecture:
        - Enforces update_working_state as mandatory tool call
        - Supports multiple tool calls per iteration (up to 7)
        - Validates minimum 2 calls per iteration
        - Extracts and stores state separately
        - Executes all tools in parallel using asyncio.gather()
        - Injects user response as the result of the previous message tool
        - Handles batch question collection from decomposer

        Returns the final message to send to the user.
        """
        logger.info("=" * 80)
        logger.info(f"USER: {user_message}")

        # Check if we're in batch question collection mode
        current_state = conversation_service.get_conversation_state(self.user_id)
        batch_active = getattr(current_state, "batch_questions_active", False)
        batch_just_completed = False

        if batch_active:
            logger.info("📋 Batch question collection mode active")
            batch_result = await self._continue_batch_question_collection(user_message)

            # If batch_result is None, it means all questions are answered
            # and we should continue to normal ReAct loop
            if batch_result is not None:
                return batch_result
            # else: fall through to normal processing below
            batch_just_completed = True

        # Inject user response into last message tool if applicable
        self._inject_user_response_into_last_message_tool(user_message)

        # Save user message to history (skip if we just saved it in batch completion)
        if not batch_just_completed:
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

                # Borrow LLM from pool and invoke
                response = await self._borrow_llm_and_invoke(messages, iteration)

                if response is None:
                    # Error occurred during LLM invocation
                    final_response = "I'm experiencing high demand right now. Please try again in a moment."
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

                # Validate tool calls
                self._validate_tool_calls(response.tool_calls)

                # Execute all tools in parallel
                tool_calls_record, tool_messages = (
                    await self._execute_tools_in_parallel(response.tool_calls)
                )

                # Add tool messages to conversation
                messages.extend(tool_messages)

                # Check if any tool was a message tool (end of iteration)
                final_response = self._check_for_message_tool_result(tool_calls_record)

                # Save tool calls record to state for next iteration
                conversation_service.update_conversation_state(
                    self.user_id, {"last_tool_calls": tool_calls_record}
                )

                if final_response:
                    # Message tool was called - end iteration
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
            "reset_conversation_state": reset_conversation_state,
            # Task decomposition
            "talk_to_decomposer_agent": talk_to_decomposer_agent,
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

            # Add trace logging for decomposer interactions
            if tool_name == "talk_to_decomposer_agent" and isinstance(result, dict):
                result_type = result.get("type")
                logger.info(f"🤖 Decomposer returned type: {result_type}")
                if result_type == "batch_questions":
                    logger.info(f"   Questions: {len(result.get('questions', []))}")
                elif result_type == "final_plan":
                    breakdown = result.get("breakdown", {})
                    logger.info(f"   Subtasks: {len(breakdown.get('subtasks', []))}")

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
