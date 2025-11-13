"""
Context management for tool execution.

Uses Python's contextvars to provide async-safe access to the current user_id
without exposing it as a tool parameter to the LLM.
"""

from contextvars import ContextVar, Token
from typing import Optional

# Context variable to track the current user_id during tool execution
current_user_id: ContextVar[Optional[str]] = ContextVar("current_user_id", default=None)


def set_current_user_id(user_id: str) -> Token[Optional[str]]:
    """
    Set the current user_id for the execution context.

    Args:
        user_id: The user ID to set

    Returns:
        Token that can be used to reset the context
    """
    return current_user_id.set(user_id)


def reset_current_user_id(token: Token[Optional[str]]) -> None:
    """
    Reset the user_id context to its previous value.

    Args:
        token: Token returned from set_current_user_id
    """
    current_user_id.reset(token)


def get_current_user_id() -> str:
    """
    Get the current user_id from the execution context.

    Returns:
        The current user_id

    Raises:
        RuntimeError: If user_id has not been set in the context
    """
    user_id = current_user_id.get()
    if user_id is None:
        raise RuntimeError(
            "current_user_id not set in tool execution context. "
            "Ensure set_current_user_id() is called before tool execution."
        )
    return user_id
