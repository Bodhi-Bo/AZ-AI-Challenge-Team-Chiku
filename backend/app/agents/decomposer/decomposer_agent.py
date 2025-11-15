"""
Decomposer Agent - Autonomous task breakdown specialist.

This agent engages in dialogue to clarify task scope before generating detailed plans.
It uses two tools to signal intent:
1. ask_for_more_information: Ask the main agent/user for clarification
2. submit_final_plan: Submit the completed task breakdown
"""

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import logging
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.services.openai_llmpool_service import llmpool
from app.utils.token_util import num_tokens_from_messages
from app.agent_tools.decomposer_action_tools import (
    ask_for_more_information,
    submit_final_plan,
)

# Configure logging
logger = logging.getLogger(__name__)


class DecomposerAgent:
    """
    Autonomous agent specialized in task decomposition.

    Engages in dialogue to clarify task scope before generating detailed plans.
    Uses world knowledge to create specific, actionable subtasks when possible.
    """

    def __init__(self):
        """Initialize the decomposer agent with its tools."""
        self.tools = [
            ask_for_more_information,
            submit_final_plan,
        ]

        self.system_prompt = self._load_system_prompt()
        logger.info("Initialized DecomposerAgent")

    def _load_system_prompt(self) -> str:
        """Load the system prompt from the prompt file."""
        prompt_file = Path(__file__).parent / "decomposer_prompt.txt"
        try:
            with open(prompt_file, "r") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {prompt_file}")
            raise RuntimeError("Decomposer prompt file is missing.")

    async def process_request(
        self,
        task_description: str,
        deadline: Optional[str] = None,
        context_dict: Optional[Dict[str, Any]] = None,
        answers_to_previous_questions: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Process a decomposition request, potentially asking follow-up questions.

        Args:
            task_description: The main task to decompose
            deadline: Optional deadline
            context_dict: Optional context information
            answers_to_previous_questions: Previous Q&A collected so far in this decomposition session

        Returns:
            Either batch questions or a final plan
        """
        logger.info("=" * 60)
        logger.info("DECOMPOSER AGENT: Processing request")
        logger.info(f"Task: {task_description}")
        logger.info(f"Deadline: {deadline}")
        logger.info(f"Context: {context_dict}")
        logger.info(
            f"Answers to previous questions: {len(answers_to_previous_questions) if answers_to_previous_questions else 0} answers"
        )

        # Build the input message by formatting the template
        # Create context text
        context_text = json.dumps(context_dict or {}, indent=2)

        # Create answers text
        answers_text = ""
        if answers_to_previous_questions:
            answers_text = "\n".join(
                [
                    f"Q: {qa.get('question', '')}\nA: {qa.get('answer', '')}"
                    for qa in answers_to_previous_questions
                ]
            )
        else:
            answers_text = "No previous answers"

        # Replace template placeholders in system prompt
        formatted_prompt = (
            self.system_prompt.replace(
                "{{task_description}}",
                task_description or "No task description provided",
            )
            .replace("{{deadline}}", deadline or "No deadline specified")
            .replace("{{context_dict}}", context_text)
            .replace("{{answers_to_previous_questions}}", answers_text)
        )

        # Build messages for LLM
        messages: List[Any] = [
            SystemMessage(content=formatted_prompt),
            HumanMessage(
                content="Analyze the task and decide: ask_for_more_information or submit_final_plan?"
            ),
        ]

        try:
            # Calculate tokens needed
            tokens_needed = num_tokens_from_messages(messages, model_name="gpt-4o")
            tokens_needed += 4000  # Increased buffer for detailed breakdown response

            logger.info(
                f"Token allocation: {tokens_needed} tokens (prompt + 4000 buffer)"
            )

            # Borrow LLM from pool
            slot, lock_token = await llmpool.borrow_llm(tokens_needed)
            llm_with_tools = slot.llm.bind_tools(self.tools)

            logger.debug(f"Borrowed LLM slot '{slot.name}' for decomposer")

            # Call LLM with tools (async)
            response = await llm_with_tools.ainvoke(messages)

            # Log raw response for debugging
            logger.debug("=" * 60)
            logger.debug("RAW LLM RESPONSE:")
            logger.debug(f"Response type: {type(response)}")
            logger.debug(
                f"Response content: {response.content if hasattr(response, 'content') else 'N/A'}"
            )
            logger.debug(
                f"Tool calls count: {len(response.tool_calls) if hasattr(response, 'tool_calls') else 0}"
            )
            if hasattr(response, "response_metadata"):
                logger.debug(
                    f"Response metadata: {json.dumps(response.response_metadata, indent=2, default=str)}"
                )
            logger.debug("=" * 60)

            # Track token usage
            actual_tokens = tokens_needed
            if hasattr(response, "response_metadata"):
                usage = response.response_metadata.get("token_usage", {})
                if usage:
                    actual_tokens = usage.get("prompt_tokens", 0) + usage.get(
                        "completion_tokens", 0
                    )
                    logger.info(
                        f"Actual token usage: {actual_tokens} tokens (prompt: {usage.get('prompt_tokens', 0)}, completion: {usage.get('completion_tokens', 0)})"
                    )

                    # Check for finish reason
                    finish_reason = response.response_metadata.get(
                        "finish_reason", "unknown"
                    )
                    logger.info(f"Finish reason: {finish_reason}")
                    if finish_reason == "length":
                        logger.warning("⚠️  Response was truncated due to length limit!")

            llmpool.record_slot_usage(slot, actual_tokens)
            llmpool.return_llm(slot, lock_token)

            # Check if tools were called
            if not response.tool_calls:
                logger.error("Decomposer didn't call any tools - protocol violation")
                logger.error(
                    f"Response content: {response.content if hasattr(response, 'content') else 'N/A'}"
                )
                return {
                    "success": False,
                    "error": "Decomposer failed to use required tools",
                    "type": "error",
                }

            # Process the tool call
            tool_call = response.tool_calls[0]
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            logger.info(f"Decomposer called: {tool_name}")
            logger.info(f"Raw tool_call structure:")
            logger.info(json.dumps(tool_call, indent=2, default=str))
            logger.info(
                f"Tool args keys: {list(tool_args.keys()) if tool_args else 'empty dict'}"
            )
            if tool_args:
                logger.info(f"Tool args size: ~{len(json.dumps(tool_args))} characters")

            if tool_name == "ask_for_more_information":
                questions = tool_args.get("questions", [])
                logger.info(f"📋 Batch questions: {len(questions)} question(s)")
                for i, q in enumerate(questions, 1):
                    logger.debug(f"  Q{i}: {q.get('question', '???')[:60]}...")

                return {
                    "success": True,
                    "type": "batch_questions",
                    "questions": questions,
                    "awaiting_responses": True,
                }

            elif tool_name == "submit_final_plan":
                # Tool args already contain the breakdown fields directly
                main_task = tool_args.get("main_task", {})
                subtasks = tool_args.get("subtasks", [])

                logger.info(
                    f"✓ Final plan submitted: {main_task.get('title', 'Untitled')}"
                )

                # Assemble breakdown from tool_args
                breakdown = {
                    "main_task": main_task,
                    "subtasks": subtasks,
                    "quick_wins": tool_args.get("quick_wins", []),
                    "high_focus_tasks": tool_args.get("high_focus_tasks", []),
                    "low_energy_tasks": tool_args.get("low_energy_tasks", []),
                    "suggested_breaks": tool_args.get("suggested_breaks", []),
                }

                # Log the entire breakdown for debugging
                logger.debug("Full breakdown structure assembled from tool args:")
                logger.debug(json.dumps(breakdown, indent=2, default=str))

                # Validate the breakdown
                if not self._validate_breakdown(breakdown):
                    logger.error("Invalid breakdown structure")
                    logger.error("Full breakdown that failed validation:")
                    logger.error(json.dumps(breakdown, indent=2, default=str))
                    return {
                        "success": False,
                        "error": "Invalid breakdown structure",
                        "type": "error",
                    }

                return {
                    "success": True,
                    "type": "final_plan",
                    "breakdown": breakdown,
                    "summary": {
                        "title": breakdown["main_task"]["title"],
                        "total_subtasks": len(breakdown["subtasks"]),
                        "total_time_minutes": breakdown["main_task"][
                            "total_estimated_time_minutes"
                        ],
                        "quick_wins_count": len(breakdown.get("quick_wins", [])),
                        "plan_feasibility": breakdown["main_task"].get(
                            "plan_feasibility", "realistic"
                        ),
                    },
                }

            else:
                logger.error(f"Unknown tool called by decomposer: {tool_name}")
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}",
                    "type": "error",
                }

        except Exception as e:
            logger.error(f"Error in decomposer agent: {e}", exc_info=True)
            return {"success": False, "error": str(e), "type": "error"}

    def _validate_breakdown(self, breakdown: Dict[str, Any]) -> bool:
        """Validate that the breakdown has the required structure."""
        try:
            # Check main_task
            if "main_task" not in breakdown:
                logger.error("Validation failed: missing 'main_task'")
                return False

            main_task = breakdown["main_task"]
            required_main = ["title", "description", "total_estimated_time_minutes"]
            missing_main = [field for field in required_main if field not in main_task]
            if missing_main:
                logger.error(
                    f"Validation failed: main_task missing fields: {missing_main}"
                )
                logger.error(f"main_task keys present: {list(main_task.keys())}")
                return False

            # Check subtasks
            if "subtasks" not in breakdown:
                logger.error("Validation failed: missing 'subtasks'")
                return False

            if not isinstance(breakdown["subtasks"], list):
                logger.error(
                    f"Validation failed: 'subtasks' is not a list, got {type(breakdown['subtasks'])}"
                )
                return False

            if len(breakdown["subtasks"]) == 0:
                logger.error("Validation failed: 'subtasks' list is empty")
                return False

            # Validate each subtask has minimum required fields
            required_subtask = [
                "id",
                "title",
                "description",
                "estimated_time_minutes",
                "order",
                "priority",
            ]
            for i, subtask in enumerate(breakdown["subtasks"]):
                missing_subtask = [
                    field for field in required_subtask if field not in subtask
                ]
                if missing_subtask:
                    logger.error(
                        f"Validation failed: subtask {i} (id={subtask.get('id', '???')}) missing fields: {missing_subtask}"
                    )
                    logger.error(f"Subtask {i} keys present: {list(subtask.keys())}")
                    return False

            logger.info("✓ Breakdown validation passed")
            return True

        except Exception as e:
            logger.error(f"Validation error: {e}", exc_info=True)
            return False


# Singleton instance
_decomposer_agent = None


def get_decomposer_agent() -> DecomposerAgent:
    """Get the singleton decomposer agent instance."""
    global _decomposer_agent
    if _decomposer_agent is None:
        _decomposer_agent = DecomposerAgent()
    return _decomposer_agent
