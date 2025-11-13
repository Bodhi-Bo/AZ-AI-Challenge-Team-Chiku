"""
State management tools for conversation context and user profile.
"""

from langchain_core.tools import tool
import logging
from typing import Dict, Any
from app.services.conversation_service import conversation_service
from app.agent.tool_context import get_current_user_id

# Configure logging
logger = logging.getLogger(__name__)


@tool
async def update_working_state(state_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update your internal working state based on conversation history and tool results.

    **CRITICAL: This MUST be the first tool you call in every iteration.**

    Synthesize insights from:
    - {{last_state_json}}: Your previous state
    - {{last_tool_actions_and_result}}: Results from your last tool calls
    - Current user message and context

    State Schema:
    Required fields:
    - intent: {high_level_goal, current_objective, priority}
    - reasoning: (string) Your thought process for this iteration

    Recommended optional fields:
    - context: {emotional_state, time_horizon, constraints, preferences}
    - planning: {missing_info, next_microstep, anticipated_user_response}
    - commitments: [{type, id, status, summary}, ...]
    - confidence: 0.0-1.0

    You can add ANY custom fields that help you track state effectively.
    Examples: emotional_trajectory, conversation_phase, user_patterns, etc.

    Args:
        state_dict: Your updated working state with insights from last iteration

    Returns:
        dict: Confirmation of state update
    """
    user_id = get_current_user_id()
    logger.info("=" * 60)
    logger.info("TOOL: update_working_state")
    logger.info(f"User ID: {user_id}")
    logger.info(f"State update: {state_dict}")

    # Validate required fields
    if "intent" not in state_dict:
        logger.warning("Missing required field: intent")
        return {
            "success": False,
            "error": "Missing required field: intent",
        }

    if "reasoning" not in state_dict:
        logger.warning("Missing required field: reasoning")
        return {
            "success": False,
            "error": "Missing required field: reasoning",
        }

    # Actually persist the state update to conversation service
    conversation_service.update_conversation_state(user_id, state_dict)

    logger.info(f"✓ State persisted to conversation service")
    logger.info(
        f"  Intent: {state_dict.get('intent', {}).get('current_objective', 'N/A')}"
    )
    logger.info(f"  Reasoning: {state_dict.get('reasoning', 'N/A')[:100]}...")

    return {
        "success": True,
        "message": "State updated and persisted successfully",
    }


@tool
async def update_user_profile(profile_updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the persistent user profile with learnings from the conversation.

    Call this tool when you've learned something valuable about the user that should
    be remembered across conversations. This is especially important before sending
    a declarative message that ends the conversation.

    **What to track in user_profile:**
    - preferences: Scheduling preferences, communication style, activity preferences
    - patterns: When they're most productive, sleep schedule, exercise routines
    - routines: Regular activities, daily/weekly patterns
    - constraints: Recurring commitments, time blocks
    - emotional_triggers: What stresses them, what helps them focus
    - productivity_windows: Best times for focused work, meetings, breaks
    - wellbeing: Exercise habits, self-care routines, dietary preferences
    - social: Social preferences, interaction patterns

    This profile persists across conversations and helps you provide better support.

    Args:
        profile_updates: Dictionary of profile fields to update (merges with existing profile)

    Returns:
        dict: Confirmation of profile update
    """
    user_id = get_current_user_id()
    logger.info("=" * 60)
    logger.info("TOOL: update_user_profile")
    logger.info(f"User ID: {user_id}")
    logger.info(f"Profile updates: {profile_updates}")

    # Get current state
    current_state = conversation_service.get_conversation_state(user_id)
    current_profile = current_state.user_profile.copy()

    # Deep merge the updates
    updated_profile = conversation_service._deep_merge(current_profile, profile_updates)

    # Update the profile
    conversation_service.update_conversation_state(
        user_id, {"user_profile": updated_profile}
    )

    logger.info(f"✓ User profile updated")
    logger.info(f"  Profile now contains: {list(updated_profile.keys())}")

    return {
        "success": True,
        "message": "User profile updated successfully",
        "profile_keys": list(updated_profile.keys()),
    }
