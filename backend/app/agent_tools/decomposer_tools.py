"""
Task decomposition tools for breaking complex tasks into ADHD-friendly subtasks.
"""

from langchain_core.tools import tool
import logging
import json
from typing import Dict, Any, Optional
from app.services.conversation_service import conversation_service
from app.agent_tools.tool_context import get_current_user_id
from app.agents.decomposer.decomposer_agent import get_decomposer_agent

# Configure logging
logger = logging.getLogger(__name__)


@tool
async def talk_to_decomposer_agent(
    task_description: str,
    deadline: Optional[str] = None,
    context_dict: Optional[Dict[str, Any]] = None,
    answers_to_previous_questions: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Engage with the decomposer agent for task breakdown.

    The decomposer agent is a specialist that will:
    1. Ask follow-up questions if the task scope is unclear
    2. Generate detailed ADHD-friendly task breakdowns once it has enough info

    **When to use this tool:**
    - User feels overwhelmed by a large task
    - User asks "how do I start?" or "what should I do first?"
    - Complex project needs to be broken down (e.g., "study for exam", "write paper", "plan trip")
    - User needs help prioritizing when time is limited

    **How it works:**
    - First call: You provide initial task description (decomposer may return batch questions)
    - If batch questions returned: Store them in decomposer state, collect ALL answers from user
    - Next call: Pass the decomposer state with all collected answers
    - Decomposer reads previous answers and either asks more questions or returns final plan

    **Integration with conversation:**
    The decomposer state in your working_state tracks the interaction:
    - decomposer.batch_questions: Questions from decomposer
    - decomposer.batch_answers: Collected answers [{question, answer}, ...]
    - When all answers collected: Pass decomposer state to this tool

    Args:
        task_description: Natural language description of the main task or project
        deadline: Optional deadline in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        context_dict: Optional dict with the full working_state from the agent.
                     The decomposer will extract what it needs from this state,
                     including the decomposer.batch_answers field.
                     If not provided, will fetch current conversation state.
        answers_to_previous_questions: JSON string of answers collected so far
                                      Format: [{"question": "...", "answer": "..."}]
                                      This is typically extracted from context_dict.decomposer.batch_answers
                                      but can be provided explicitly if needed

    Returns:
        dict: Either:
            - {"questions": [...], "awaiting_responses": True} - More questions needed
            - {"breakdown": {...}, "summary": {...}} - Final plan ready

    Example flow:
        # First call
        result = talk_to_decomposer_agent(
            task_description="Study for biology exam",
            deadline="2025-11-20"
        )
        # Returns: {"questions": [Q1, Q2, Q3], "awaiting_responses": True}

        # Collect all 3 answers, store in decomposer state

        # Second call with all answers
        result = talk_to_decomposer_agent(
            task_description="Study for biology exam",
            deadline="2025-11-20",
            context_dict={"decomposer": {"batch_answers": [
                {"question": "Which chapters?", "answer": "chapters 1-2"},
                {"question": "Starting from scratch?", "answer": "yes"},
                {"question": "Time available?", "answer": "3 hours"}
            ]}}
        )
        # Returns: {"breakdown": {...}} or more questions if needed
    """

    user_id = get_current_user_id()
    logger.info("=" * 60)
    logger.info("TOOL: talk_to_decomposer_agent")
    logger.info(f"User ID: {user_id}")
    logger.info(f"Task: {task_description}")
    logger.info(f"Deadline: {deadline}")
    logger.info(f"Context provided: {context_dict is not None}")
    logger.info(
        f"Answers to previous questions provided: {answers_to_previous_questions is not None}"
    )

    try:
        # If no context_dict provided, get current conversation state
        if context_dict is None:
            logger.info("No context_dict provided, fetching current conversation state")
            current_state = conversation_service.get_conversation_state(user_id)
            # Convert state object to dict if needed
            if hasattr(current_state, "__dict__"):
                context_dict = current_state.__dict__
            elif isinstance(current_state, dict):
                context_dict = current_state
            else:
                context_dict = {}
            logger.info(
                f"Retrieved state keys: {list(context_dict.keys()) if context_dict else 'empty'}"
            )
        else:
            logger.info(
                f"Using provided context_dict with keys: {list(context_dict.keys())}"
            )

        # Extract answers from context_dict.decomposer.batch_answers if not explicitly provided
        parsed_answers = None
        if answers_to_previous_questions:
            try:
                parsed_answers = json.loads(answers_to_previous_questions)
                logger.info(
                    f"Parsed answers_to_previous_questions: {len(parsed_answers)} answers"
                )
            except json.JSONDecodeError:
                logger.warning(
                    f"Failed to parse answers_to_previous_questions as JSON: {answers_to_previous_questions}"
                )
        elif context_dict and "decomposer" in context_dict:
            # Extract from decomposer state
            decomposer_state = context_dict.get("decomposer", {})
            batch_answers = decomposer_state.get("batch_answers", [])
            if batch_answers:
                parsed_answers = batch_answers
                logger.info(
                    f"Extracted {len(parsed_answers)} answers from decomposer state"
                )

        # Get the decomposer agent and process the request
        decomposer = get_decomposer_agent()
        result = await decomposer.process_request(
            task_description=task_description,
            deadline=deadline,
            context_dict=context_dict,
            answers_to_previous_questions=parsed_answers,
        )

        result_type = result.get("type", "unknown")
        logger.info(f"Decomposer result type: {result_type}")

        # Log schema details for verification
        if result_type == "batch_questions":
            logger.info(f"  Questions count: {len(result.get('questions', []))}")
        elif result_type == "final_plan":
            breakdown = result.get("breakdown", {})
            main_task = breakdown.get("main_task", {})
            logger.info(f"  Plan title: {main_task.get('title', 'N/A')}")
            logger.info(f"  Subtasks: {len(breakdown.get('subtasks', []))}")

        return result

    except Exception as e:
        logger.error(f"Error in talk_to_decomposer_agent: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "type": "error",
            "message": "Failed to communicate with decomposer agent. Please try again.",
        }
