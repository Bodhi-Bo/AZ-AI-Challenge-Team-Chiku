"""
Task decomposition tools for breaking complex tasks into ADHD-friendly subtasks.
"""

from langchain_core.tools import tool
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.utils.ask_gpt_util import ask_gpt_async
from app.models.gpt_model import GPT_4o_mini, ModelParameters
from app.services.conversation_service import conversation_service
from app.agent.tool_context import get_current_user_id

# Configure logging
logger = logging.getLogger(__name__)


def _load_decomposer_prompt() -> str:
    """Load the decomposer prompt template from file."""
    try:
        with open("app/agent/decomposer_prompt.txt", "r") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load decomposer_prompt.txt: {e}")
        raise ValueError("Decomposer prompt file not found")


def _extract_context_from_state(
    state: Any, deadline: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract and map the conversation state to the decomposer input schema.

    Maps from working_state fields to decomposer's expected context structure.
    """
    context_dict = {
        "task_type": "unknown",
        "importance": "medium",
        "user_emotional_state": "unknown",
        "known_difficulties": [],
        "preferences": {
            "preferred_session_length_minutes": 20,
            "best_time_of_day": "flexible",
            "avoid_task_types": [],
            "body_doubling_available": False,
        },
        "time_constraints": {},
    }

    # Extract from state.context if it exists
    if hasattr(state, "context") and state.context:
        state_context = state.context

        # Map emotional_state
        if isinstance(state_context, dict) and "emotional_state" in state_context:
            emotion = state_context["emotional_state"]
            # Map to decomposer's emotional states
            emotion_map = {
                "stressed": "overwhelmed",
                "tired": "overwhelmed",
                "calm": "neutral",
                "focused": "energized",
                "confused": "anxious",
                "lost": "overwhelmed",
                "motivated": "energized",
            }
            context_dict["user_emotional_state"] = emotion_map.get(
                emotion.lower(), emotion.lower()
            )

        # Map time_horizon to time_constraints
        if isinstance(state_context, dict) and "time_horizon" in state_context:
            horizon = state_context["time_horizon"]
            # Try to infer available minutes from horizon
            if "today" in horizon.lower():
                # Assume rest of today
                now = datetime.now()
                end_of_day = now.replace(hour=23, minute=59, second=59)
                available_minutes = int((end_of_day - now).total_seconds() / 60)
                context_dict["time_constraints"][
                    "approx_available_minutes_before_deadline"
                ] = available_minutes
            elif "week" in horizon.lower():
                context_dict["time_constraints"][
                    "approx_available_minutes_before_deadline"
                ] = 2400  # ~40 hours
            elif deadline:
                # Calculate from deadline
                try:
                    deadline_dt = datetime.fromisoformat(
                        deadline.replace("Z", "+00:00")
                    )
                    now = datetime.now()
                    if deadline_dt > now:
                        available_minutes = int(
                            (deadline_dt - now).total_seconds() / 60
                        )
                        context_dict["time_constraints"][
                            "approx_available_minutes_before_deadline"
                        ] = available_minutes
                except:
                    pass

        # Extract constraints as difficulties
        if isinstance(state_context, dict) and "constraints" in state_context:
            constraints = state_context["constraints"]
            if isinstance(constraints, list):
                # Map constraints to known_difficulties
                difficulty_keywords = {
                    "overwhelm": "task_initiation",
                    "focus": "time_blindness",
                    "perfect": "perfectionism",
                    "decide": "decision_fatigue",
                    "initiat": "task_initiation",
                }
                for constraint in constraints:
                    if isinstance(constraint, str):
                        constraint_lower = constraint.lower()
                        for keyword, difficulty in difficulty_keywords.items():
                            if (
                                keyword in constraint_lower
                                and difficulty not in context_dict["known_difficulties"]
                            ):
                                context_dict["known_difficulties"].append(difficulty)

        # Extract preferences
        if isinstance(state_context, dict) and "preferences" in state_context:
            prefs = state_context["preferences"]
            if isinstance(prefs, dict):
                if "session_length" in prefs:
                    try:
                        context_dict["preferences"][
                            "preferred_session_length_minutes"
                        ] = int(prefs["session_length"])
                    except:
                        pass
                if "best_time_of_day" in prefs:
                    context_dict["preferences"]["best_time_of_day"] = prefs[
                        "best_time_of_day"
                    ]
                if "avoid_task_types" in prefs:
                    context_dict["preferences"]["avoid_task_types"] = prefs[
                        "avoid_task_types"
                    ]

    # Extract from intent for task_type and importance
    if hasattr(state, "intent") and state.intent:
        intent = state.intent
        if isinstance(intent, dict):
            # Map priority to importance
            priority = intent.get("priority", "medium")
            context_dict["importance"] = priority

            # Try to infer task_type from high_level_goal
            goal = intent.get("high_level_goal", "").lower()
            if any(
                word in goal
                for word in ["study", "homework", "assignment", "class", "learn"]
            ):
                context_dict["task_type"] = "academic"
            elif any(
                word in goal for word in ["work", "project", "meeting", "presentation"]
            ):
                context_dict["task_type"] = "professional"
            elif any(word in goal for word in ["schedule", "calendar", "organize"]):
                context_dict["task_type"] = "admin"
            elif any(
                word in goal for word in ["personal", "exercise", "health", "wellbeing"]
            ):
                context_dict["task_type"] = "personal"

    # Extract from user_profile if available
    if hasattr(state, "user_profile") and state.user_profile:
        profile = state.user_profile
        if isinstance(profile, dict):
            # Extract preferences from profile
            if "preferences" in profile and isinstance(profile["preferences"], dict):
                profile_prefs = profile["preferences"]
                if "best_time_of_day" in profile_prefs:
                    context_dict["preferences"]["best_time_of_day"] = profile_prefs[
                        "best_time_of_day"
                    ]
                if "session_length" in profile_prefs:
                    try:
                        context_dict["preferences"][
                            "preferred_session_length_minutes"
                        ] = int(profile_prefs["session_length"])
                    except:
                        pass

            # Extract known difficulties from profile patterns
            if "patterns" in profile and isinstance(profile["patterns"], dict):
                patterns = profile["patterns"]
                if "adhd_challenges" in patterns and isinstance(
                    patterns["adhd_challenges"], list
                ):
                    for challenge in patterns["adhd_challenges"]:
                        if challenge not in context_dict["known_difficulties"]:
                            context_dict["known_difficulties"].append(challenge)

    # Default to common ADHD difficulties if none extracted
    if not context_dict["known_difficulties"]:
        context_dict["known_difficulties"] = ["task_initiation", "time_blindness"]

    return context_dict


def _validate_decomposer_output(response_text: str) -> Dict[str, Any]:
    """
    Parse and validate the JSON response from the decomposer LLM.

    Raises ValueError if validation fails.
    Returns the parsed and validated JSON.
    """
    try:
        # Remove markdown code blocks if present
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # Parse JSON
        data = json.loads(cleaned)

        # Validate required top-level fields
        required_fields = [
            "main_task",
            "subtasks",
            "quick_wins",
            "high_focus_tasks",
            "low_energy_tasks",
            "suggested_breaks",
        ]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Validate main_task structure
        main_task = data["main_task"]
        required_main_task_fields = [
            "title",
            "description",
            "total_estimated_time_minutes",
            "overall_complexity",
            "energy_required",
        ]
        for field in required_main_task_fields:
            if field not in main_task:
                raise ValueError(f"Missing required main_task field: {field}")

        # Validate subtasks
        if not isinstance(data["subtasks"], list) or len(data["subtasks"]) == 0:
            raise ValueError("subtasks must be a non-empty list")

        for i, subtask in enumerate(data["subtasks"]):
            required_subtask_fields = [
                "id",
                "title",
                "description",
                "estimated_time_minutes",
                "complexity",
                "energy_level",
                "order",
                "priority",
            ]
            for field in required_subtask_fields:
                if field not in subtask:
                    raise ValueError(f"Subtask {i} missing required field: {field}")

            # Validate estimated_time_minutes <= 30
            if subtask["estimated_time_minutes"] > 30:
                logger.warning(
                    f"Subtask {i} ({subtask['id']}) exceeds 30 minutes: {subtask['estimated_time_minutes']}"
                )
                # Don't fail, just warn

        # Validate that all referenced task IDs in quick_wins, high_focus_tasks, low_energy_tasks exist
        all_task_ids = {subtask["id"] for subtask in data["subtasks"]}

        for task_id in data["quick_wins"]:
            if task_id not in all_task_ids:
                raise ValueError(
                    f"quick_wins references non-existent task_id: {task_id}"
                )

        for task_id in data["high_focus_tasks"]:
            if task_id not in all_task_ids:
                raise ValueError(
                    f"high_focus_tasks references non-existent task_id: {task_id}"
                )

        for task_id in data["low_energy_tasks"]:
            if task_id not in all_task_ids:
                raise ValueError(
                    f"low_energy_tasks references non-existent task_id: {task_id}"
                )

        # Validate dependencies reference existing tasks
        for subtask in data["subtasks"]:
            if "dependencies" in subtask:
                for dep_id in subtask["dependencies"]:
                    if dep_id not in all_task_ids:
                        raise ValueError(
                            f"Subtask {subtask['id']} has invalid dependency: {dep_id}"
                        )

        logger.info(
            f"✓ Validation passed: {len(data['subtasks'])} subtasks, {data['main_task']['total_estimated_time_minutes']} min total"
        )
        return data

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        logger.error(f"Response text: {response_text[:500]}")
        raise ValueError(f"Invalid JSON response from decomposer: {e}")
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise ValueError(f"Decomposer output validation failed: {e}")


@tool
async def decompose_task(
    task_description: str,
    deadline: Optional[str] = None,
    context_dict: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Break down a complex task into small, ADHD-friendly subtasks with clear structure and emotional safety.

    This tool uses specialized AI to decompose tasks into:
    - Subtasks ≤ 30 minutes each
    - Clear, actionable steps with simple language
    - Priority levels (essential/helpful_extra/stretch_option)
    - ADHD strategies, rewards, and transition times
    - Quick wins, high-focus tasks, and low-energy tasks
    - Suggested breaks

    The decomposition respects time constraints and user's emotional state.

    **When to use this tool:**
    - User feels overwhelmed by a large task
    - User asks "how do I start?" or "what should I do first?"
    - Complex project needs to be broken down (e.g., "study for exam", "write paper", "plan trip")
    - User needs help prioritizing when time is limited

    **Integration with scheduling:**
    After decomposing, you can help the user schedule the subtasks using your calendar tools.
    The decomposer provides time estimates and energy levels to help with smart scheduling.

    Args:
        task_description: Natural language description of the main task or project
        deadline: Optional deadline in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS) or natural language
        context_dict: Optional dict with any relevant context. The decomposer will intelligently extract
                     what it needs. Can include fields like:
                     - task_type, importance, user_emotional_state, known_difficulties, preferences,
                       time_constraints, or any other relevant information from working_state
                     - If not provided, will be extracted from current conversation state

    Returns:
        dict: Structured task breakdown with main_task, subtasks, quick_wins, high_focus_tasks,
              low_energy_tasks, and suggested_breaks

    Example:
        decompose_task(
            task_description="Write a 5-page research paper on climate change",
            deadline="2025-11-20",
            context_dict={
                "user_emotional_state": "overwhelmed",
                "importance": "high",
                "time_constraints": {"approx_available_minutes_before_deadline": 480},
                "preferences": {"preferred_session_length_minutes": 25, "best_time_of_day": "morning"}
            }
        )

        # Or just let it extract from state:
        decompose_task(
            task_description="Study for biology exam chapters 5-8",
            deadline="2025-11-21"
        )
    """
    user_id = get_current_user_id()
    logger.info("=" * 60)
    logger.info("TOOL: decompose_task")
    logger.info(f"User ID: {user_id}")
    logger.info(f"Task: {task_description}")
    logger.info(f"Deadline: {deadline}")
    logger.info(f"Context provided: {context_dict is not None}")

    try:
        # Load the decomposer system prompt
        system_prompt = _load_decomposer_prompt()

        # Determine context to use
        if context_dict is None:
            # Extract context from current conversation state
            logger.info("No context_dict provided, extracting from conversation state")
            current_state = conversation_service.get_conversation_state(user_id)
            context_dict = _extract_context_from_state(current_state, deadline)
            logger.info(
                f"Extracted context from state: {json.dumps(context_dict, indent=2)}"
            )
        else:
            logger.info(
                f"Using provided context_dict: {json.dumps(context_dict, indent=2)}"
            )

        # Build the input for the decomposer
        # The decomposer prompt expects a specific structure, but we'll pass along
        # whatever context we have and let it intelligently extract what it needs
        decomposer_input = {
            "task_description": task_description,
            "deadline": deadline,
            "context": context_dict,
        }

        input_json = json.dumps(decomposer_input, indent=2)

        logger.info(f"Calling decomposer LLM with input:")
        logger.info(input_json)

        # Call the decomposer LLM using the keypool
        model_params = ModelParameters(
            temperature=0.7,  # Some creativity for better subtask generation
            max_tokens=2000,  # Enough for comprehensive breakdown
        )

        response_text = await ask_gpt_async(
            context=input_json,
            prompt=system_prompt,
            gpt_model=GPT_4o_mini,
            model_params=model_params,
        )

        if not response_text:
            raise ValueError("Decomposer LLM returned empty response")

        logger.info(
            f"Received response from decomposer LLM ({len(response_text)} chars)"
        )
        logger.debug(f"Response: {response_text[:500]}...")

        # Parse and validate the response
        validated_output = _validate_decomposer_output(response_text)

        logger.info(f"✓ Task decomposed successfully")
        logger.info(f"  Main task: {validated_output['main_task']['title']}")
        logger.info(f"  Subtasks: {len(validated_output['subtasks'])}")
        logger.info(
            f"  Total time: {validated_output['main_task']['total_estimated_time_minutes']} minutes"
        )
        logger.info(f"  Quick wins: {len(validated_output['quick_wins'])}")
        logger.info(
            f"  Plan feasibility: {validated_output['main_task'].get('plan_feasibility', 'N/A')}"
        )

        return {
            "success": True,
            "breakdown": validated_output,
            "summary": {
                "title": validated_output["main_task"]["title"],
                "total_subtasks": len(validated_output["subtasks"]),
                "total_time_minutes": validated_output["main_task"][
                    "total_estimated_time_minutes"
                ],
                "quick_wins_count": len(validated_output["quick_wins"]),
                "plan_feasibility": validated_output["main_task"].get(
                    "plan_feasibility", "realistic"
                ),
                "time_constraint_note": validated_output["main_task"].get(
                    "time_constraint_note"
                ),
            },
        }

    except Exception as e:
        logger.error(f"Error in decompose_task: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to decompose task. Please try rephrasing or breaking it down manually.",
        }
