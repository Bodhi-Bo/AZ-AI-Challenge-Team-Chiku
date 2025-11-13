"""
Internal class used by OpenAILLMPool to manage LLM instances using LLMSlot.
DO NOT USE THIS CLASS DIRECTLY.
"""

import logging
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from pydantic import SecretStr

from .keyslot import KeySlot

logger = logging.getLogger(__name__)


class LLMSlot:
    """
    Wraps a KeySlot and adds LLM-specific functionality.
    Delegates all Redis state management (locking, cooldown, token tracking) to KeySlot.
    """

    def __init__(
        self,
        key_slot: KeySlot,
        model_name: str,
    ):
        self.key_slot = key_slot
        self.name = key_slot.name
        self.api_key = key_slot.api_key
        self.model_name = model_name

        # Initialize the LLM instance (LLM-specific)
        self._initialize_llm()

    def _initialize_llm(self):
        """
        Initialize the ChatOpenAI instance with this slot's API key.
        This LLM instance will be reused for all requests using this slot.
        """
        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=SecretStr(self.api_key),
            temperature=0.7,
        )
        logger.debug(
            f"Initialized LLM for slot '{self.name}' with model '{self.model_name}'"
        )

    # Delegate all KeySlot methods
    @property
    def token_usage(self) -> int:
        """Delegate to KeySlot."""
        return self.key_slot.token_usage

    def record_usage(self, tokens_used: int) -> None:
        """Delegate to KeySlot."""
        self.key_slot.record_usage(tokens_used)
        logger.debug(f"Recorded {tokens_used} tokens for LLM slot '{self.name}'")

    async def acquire_lock(self, lock_expiry: float, timeout: float = 2.0) -> str:
        """Delegate to KeySlot."""
        lock_token = await self.key_slot.acquire_lock(lock_expiry, timeout)
        logger.debug(f"Acquired lock for LLM slot '{self.name}'")
        return lock_token

    def is_locked(self) -> bool:
        """Delegate to KeySlot."""
        return self.key_slot.is_locked()

    def release_lock(self, lock_token: str) -> None:
        """Delegate to KeySlot."""
        self.key_slot.release_lock(lock_token)
        logger.debug(f"Released lock for LLM slot '{self.name}'")

    @property
    def cooldown_until(self) -> float:
        """Delegate to KeySlot."""
        return self.key_slot.cooldown_until

    def set_cooldown(self, seconds: float):
        """Delegate to KeySlot."""
        self.key_slot.set_cooldown(seconds)
        logger.debug(f"Set cooldown for LLM slot '{self.name}' for {seconds} seconds")

    def mark_exhausted(self, exhausted_msg: str) -> None:
        """Delegate to KeySlot."""
        self.key_slot.mark_exhausted(exhausted_msg)
        logger.warning(f"Marked LLM slot '{self.name}' as exhausted: {exhausted_msg}")

    def mark_available(self) -> None:
        """Delegate to KeySlot."""
        self.key_slot.mark_available()
        logger.info(f"Marked LLM slot '{self.name}' as available")

    def can_accept(self, tokens_needed: int) -> bool:
        """Delegate to KeySlot."""
        return self.key_slot.can_accept(tokens_needed)

    # LLM-specific method
    async def invoke(self, messages: list[BaseMessage]) -> tuple[str, int]:
        """
        Invoke the LLM with the given messages and return the response content and token usage.
        This method handles errors and updates slot state accordingly.

        Returns:
            tuple[str, int]: (response_content, tokens_used)
        """
        try:
            response = await self.llm.ainvoke(messages)

            # Extract token usage from response metadata if available
            tokens_used = 0
            if hasattr(response, "response_metadata"):
                usage = response.response_metadata.get("token_usage", {})
                tokens_used = usage.get("prompt_tokens", 0) + usage.get(
                    "completion_tokens", 0
                )

            logger.debug(
                f"LLM slot '{self.name}' completed request. Tokens used: {tokens_used}"
            )

            # Ensure content is a string
            content = response.content
            if isinstance(content, list):
                # If content is a list, join it or take first element
                content = str(content)

            return str(content), int(tokens_used)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"LLM slot '{self.name}' encountered error: {error_msg}")

            # Handle quota exhaustion
            if (
                "You exceeded your current quota" in error_msg
                or "insufficient_quota" in error_msg
            ):
                logger.warning(
                    f"Quota exceeded for LLM slot '{self.name}'. Marking as exhausted."
                )
                self.mark_exhausted(error_msg)
                raise ValueError(f"Quota exceeded for LLM slot: {self.name}")

            # Handle rate limiting
            elif (
                "rate limit reached" in error_msg.lower()
                or "rate_limit_exceeded" in error_msg
            ):
                match = re.search(r"Please try again in ([\d.]+)s", error_msg)
                if match:
                    delay = float(match.group(1))
                    logger.warning(
                        f"Rate limit hit for LLM slot '{self.name}'. Setting {delay}s cooldown."
                    )
                    self.set_cooldown(delay)
                else:
                    logger.warning(
                        f"Rate limit hit for LLM slot '{self.name}'. Setting default 5s cooldown."
                    )
                    self.set_cooldown(5.0)

                raise ValueError(f"Rate limit hit for LLM slot: {self.name}")

            # Re-raise other errors
            raise
