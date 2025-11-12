"""
Message tools for sending user-facing messages.
These tools are special - they signal the end of an agent iteration.
"""

from langchain_core.tools import tool
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@tool
def send_interrogative_message(
    content: str, partial_state_update: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Ask the user a clarifying question.
    Use this when you need a single, small piece of information to make progress.

    Args:
        content: The question to ask the user (should be concise and kind)
        partial_state_update: Your current state insights (optional)

    Returns:
        dict: Message content and metadata
    """
    logger.info("=" * 60)
    logger.info("TOOL: send_interrogative_message")
    logger.info(f"Question: {content}")
    logger.info(f"State update: {partial_state_update}")

    return {
        "success": True,
        "message_type": "interrogative",
        "content": content,
        "partial_state_update": partial_state_update,
        "stop_iteration": True,  # Signal to halt the agent loop
    }


@tool
def send_declarative_message(
    content: str, partial_state_update: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Send a supportive message or summary to the user.
    Use this when you've completed a task or need user confirmation.
    This ends the iteration and returns control to the user.

    Args:
        content: The message to send (can be a confirmation, summary, or supportive statement)
        partial_state_update: Your current state insights (optional)

    Returns:
        dict: Message content and metadata
    """
    logger.info("=" * 60)
    logger.info("TOOL: send_declarative_message")
    logger.info(f"Message: {content}")
    logger.info(f"State update: {partial_state_update}")

    return {
        "success": True,
        "message_type": "declarative",
        "content": content,
        "partial_state_update": partial_state_update,
        "stop_iteration": True,  # Signal to halt the agent loop
    }
