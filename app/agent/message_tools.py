"""
Message tools for sending user-facing messages.
These tools send messages to the user and wait for their response.
"""

from langchain_core.tools import tool
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


@tool
def send_interrogative_message(content: str) -> Dict[str, Any]:
    """
    Ask the user a clarifying question.
    Use this when you need a single, small piece of information to make progress.

    Args:
        content: The question to ask the user (should be concise and kind)

    Returns:
        dict: Message content and metadata
    """
    logger.info("=" * 60)
    logger.info("TOOL: send_interrogative_message")
    logger.info(f"Question: {content}")

    return {
        "success": True,
        "message_type": "interrogative",
        "content": content,
    }


@tool
def send_declarative_message(content: str) -> Dict[str, Any]:
    """
    Send a supportive message or summary to the user.
    Use this when you've completed a task or need user confirmation.

    Args:
        content: The message to send (can be a confirmation, summary, or supportive statement)

    Returns:
        dict: Message content and metadata
    """
    logger.info("=" * 60)
    logger.info("TOOL: send_declarative_message")
    logger.info(f"Message: {content}")

    return {
        "success": True,
        "message_type": "declarative",
        "content": content,
    }
