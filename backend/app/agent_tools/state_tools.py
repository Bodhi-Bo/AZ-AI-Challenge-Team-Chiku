"""
State management tools for conversation context and user profile.
"""

from langchain_core.tools import tool
import logging
from typing import Dict, Any, Optional, List
from app.services.conversation_service import conversation_service
from app.agent_tools.tool_context import get_current_user_id

# Configure logging
logger = logging.getLogger(__name__)


@tool
async def update_working_state(
    reasoning: str,
    intent: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    planning: Optional[Dict[str, Any]] = None,
    commitments: Optional[List[Dict[str, Any]]] = None,
    confidence: Optional[float] = None,
    conversation_phase: Optional[str] = None,
    emotional_trajectory: Optional[List[str]] = None,
    decomposer: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Update your internal working state based on conversation history and tool results.

    **CRITICAL: This MUST be the first tool you call in every iteration.**

    Synthesize insights from:
    - {{last_state_json}}: Your previous state
    - {{last_tool_actions_and_result}}: Results from your last tool calls
    - Current user message and context

    Args:
        reasoning: (REQUIRED) Your thought process for this iteration - why you're making the calls you're making
        intent: {high_level_goal, current_objective, priority} - What the user ultimately wants and what you're working on now
        context: {emotional_state, time_horizon, constraints, preferences} - User's emotional state and situational context
        planning: {missing_info, next_microstep, anticipated_user_response} - What you need and what's next
        commitments: [{type, id, status, summary}, ...] - Events/reminders you've created or modified
        confidence: 0.0-1.0 - How certain you are about your interpretation
        conversation_phase: Current phase like "discovery", "planning", "execution", "confirmation"
        emotional_trajectory: List tracking how user's mood evolves, e.g. ["confused", "overwhelmed"]
        decomposer: {batch_questions, batch_answers, current_question_index} - State for decomposer interaction
        **kwargs: Any additional custom fields you want to track

    Returns:
        dict: Confirmation of state update
    """
    user_id = get_current_user_id()
    logger.info("=" * 60)
    logger.info("TOOL: update_working_state")
    logger.info(f"User ID: {user_id}")

    # Build state_dict from all parameters
    state_dict: Dict[str, Any] = {"reasoning": reasoning}

    if intent is not None:
        state_dict["intent"] = intent
    if context is not None:
        state_dict["context"] = context
    if planning is not None:
        state_dict["planning"] = planning
    if commitments is not None:
        state_dict["commitments"] = commitments
    if confidence is not None:
        state_dict["confidence"] = confidence
    if conversation_phase is not None:
        state_dict["conversation_phase"] = conversation_phase
    if emotional_trajectory is not None:
        state_dict["emotional_trajectory"] = emotional_trajectory
    if decomposer is not None:
        state_dict["decomposer"] = decomposer

    # Add any custom kwargs
    state_dict.update(kwargs)

    logger.info(f"State update: {state_dict}")

    # Actually persist the state update to conversation service
    conversation_service.update_conversation_state(user_id, state_dict)

    logger.info(f"✓ State persisted to conversation service")
    logger.info(
        f"  Intent: {state_dict.get('intent', {}).get('current_objective', 'N/A')}"
    )
    logger.info(f"  Reasoning: {reasoning[:100]}...")

    return {
        "success": True,
        "message": "State updated and persisted successfully",
        "state_dict": state_dict,
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


@tool
async def reset_conversation_state() -> Dict[str, Any]:
    """
    Reset the conversation state to start fresh.

    **CRITICAL: Call this tool when you send a FINAL declarative message that completes
    the user's request and ends the conversation.**

    This tool:
    - Marks all messages from the current session as old (is_old=True in DB)
    - Resets the conversation state while preserving user_profile
    - Generates a new session_id for the next conversation

    **When to call this:**
    - After sending a final declarative message confirming task completion
    - When the conversation phase is "confirmation" or "complete"
    - When the user confirms everything is done and you say goodbye

    **When NOT to call this:**
    - During ongoing conversations
    - When asking questions or awaiting user input
    - When you expect the user to continue the conversation

    Returns:
        dict: Confirmation of state reset with count of messages marked as old
    """
    user_id = get_current_user_id()
    logger.info("=" * 60)
    logger.info("TOOL: reset_conversation_state")
    logger.info(f"User ID: {user_id}")

    # Call the async reset method
    result = await conversation_service.reset_transient_state(user_id)

    logger.info(f"✓ Conversation state reset successfully")
    logger.info(f"  Messages marked as old: {result.get('messages_marked_old', 0)}")
    logger.info(f"  New session ID generated: {result.get('new_session_id', 'N/A')}")

    return {
        "success": True,
        "message": "Conversation state reset successfully - ready for next conversation",
        "messages_marked_old": result.get("messages_marked_old", 0),
        "new_session_id": result.get("new_session_id"),
    }
