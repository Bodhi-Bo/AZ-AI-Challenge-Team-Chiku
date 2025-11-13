"""
OpenAILLMPool is a singleton class that manages a pool of LLM instances (ChatOpenAI).
Each LLM instance is backed by a different API key from Redis.
Other apps/modules can import the singleton instance to use it.
"""

import asyncio
import logging
import random

from ..models.keyslot import KeySlot
from ..models.llmslot import LLMSlot
from ..utils.redis_key_manager_util import get_all_openai_keys
from ..config import OPENAI_MODEL, LOCK_EXPIRY

logger = logging.getLogger(__name__)


class OpenAILLMPool:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = OPENAI_MODEL):
        # only run once
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self.model_name = model_name
        self.initialize_slots()

    def initialize_slots(self):
        """
        Initialize LLM slots from all available OpenAI keys in Redis.
        Each slot contains a long-lived ChatOpenAI instance.
        """
        key_map = get_all_openai_keys()
        self.slots: list[LLMSlot] = []

        for name, api_key in key_map.items():
            # Create a KeySlot for this API key
            key_slot = KeySlot(name, api_key)
            # Wrap it in an LLMSlot
            llm_slot = LLMSlot(key_slot, self.model_name)
            self.slots.append(llm_slot)

        logger.info(
            f"Initialized {len(self.slots)} LLM slots with model '{self.model_name}'"
        )

    def refresh(self):
        """
        Refresh the pool by reinitializing all slots.
        Useful if keys are added/removed from Redis.
        """
        self.initialize_slots()

    async def borrow_llm(
        self,
        tokens_needed: int,
        lock_expiry: int = int(LOCK_EXPIRY),
        timeout_in_seconds: int = 0,
    ) -> tuple[LLMSlot, str]:
        """
        Borrow an LLM slot that can handle the requested number of tokens.

        Args:
            tokens_needed: Number of tokens required for this request
            lock_expiry: Lock expiry time in seconds
            timeout_in_seconds: Maximum time to wait for an available slot (0 = wait forever)

        Returns:
            tuple[LLMSlot, str]: The borrowed LLM slot and its lock token

        Raises:
            TimeoutError: If no available slot is found within timeout period
        """
        expiry = (
            asyncio.get_event_loop().time() + (timeout_in_seconds * 1000)
            if timeout_in_seconds > 0
            else None
        )

        logger.debug(f"Attempting to borrow LLM for {tokens_needed} tokens")

        while True:
            random.shuffle(self.slots)
            for slot in self.slots:
                # Check if slot can accept the request and is not locked
                if slot.can_accept(tokens_needed) and not slot.is_locked():
                    try:
                        lock_token = await slot.acquire_lock(lock_expiry)
                        logger.info(
                            f"Borrowed LLM slot '{slot.name}' for {tokens_needed} tokens"
                        )
                        return slot, lock_token
                    except Exception as e:
                        logger.error(f"Error acquiring lock for slot {slot.name}: {e}")
                        continue

            await asyncio.sleep(0.25)

            if expiry and asyncio.get_event_loop().time() > expiry:
                raise TimeoutError(
                    "No available LLM slot found within the timeout period."
                )

    def return_llm(self, slot: LLMSlot, lock_token: str) -> None:
        """
        Return a borrowed LLM slot back to the pool.

        Args:
            slot: The LLM slot to return
            lock_token: The lock token obtained when borrowing

        Raises:
            ValueError: If the lock token doesn't match
        """
        try:
            slot.release_lock(lock_token)
            logger.debug(f"Returned LLM slot '{slot.name}' to pool")
        except Exception as e:
            raise ValueError(f"Failed to release lock for slot {slot.name}: {e}") from e

    def record_slot_usage(self, slot: LLMSlot, tokens_used: int) -> None:
        """
        Record token usage for an LLM slot.
        CAUTION: This effect will be global, affecting all users of the LLM pool.

        Args:
            slot: The LLM slot that was used
            tokens_used: Number of tokens consumed
        """
        slot.record_usage(tokens_used)
        logger.debug(f"Recorded {tokens_used} tokens for slot '{slot.name}'")

    def mark_slot_exhausted(self, slot: LLMSlot, exhausted_msg: str):
        """
        Mark an LLM slot as exhausted and remove it from the pool.
        CAUTION: This effect will be global, affecting all users of the LLM pool.

        Args:
            slot: The LLM slot to mark as exhausted
            exhausted_msg: Error message explaining why the slot is exhausted

        Raises:
            RuntimeError: If all slots are exhausted
        """
        slot.mark_exhausted(exhausted_msg)
        if slot in self.slots:
            self.slots.remove(slot)
            logger.warning(f"Removed exhausted slot '{slot.name}' from pool")

        if not self.slots:
            logger.error("All LLM slots are exhausted. Stopping the process.")
            raise RuntimeError("All LLM slots are exhausted.")

    def mark_slot_available(self, slot: LLMSlot):
        """
        Mark an LLM slot as available again.
        CAUTION: This effect will be global, affecting all users of the LLM pool.

        Args:
            slot: The LLM slot to mark as available
        """
        slot.mark_available()

        # If not in pool, refresh to pick it up
        if slot not in self.slots:
            self.refresh()

    def __str__(self):
        return "\n".join(
            [f"LLMSlot(id={slot.name}, model={slot.model_name})" for slot in self.slots]
        )


# Singleton instance
llmpool = OpenAILLMPool()
