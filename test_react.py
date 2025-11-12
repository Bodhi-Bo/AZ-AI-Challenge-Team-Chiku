"""
Simple test script for the ReAct calendar agent.
Tests basic functionality without WebSocket.
"""

import asyncio
import logging
from app.agent.react_agent import create_react_agent
from app.utils.mongo_client import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def test_react_agent():
    """Test the ReAct agent with simple scenarios."""

    # Initialize MongoDB/Beanie connection FIRST
    print("Initializing database connection...")
    await init_db()
    print("✅ Database initialized!\n")

    user_id = "test_user_react"

    print("=" * 80)
    print("Testing ReAct Calendar Agent (Chiku)")
    print("=" * 80)

    # Create agent
    agent = create_react_agent(user_id)

    # Test scenarios
    scenarios = [
        # "Hi, I'm feeling a bit overwhelmed today. Can you help me?",
        # "What's on my schedule for today?",
        "Can you schedule a meeting with my team tomorrow at 2pm for 60 minutes?",
    ]

    for i, message in enumerate(scenarios, 1):
        print(f"\n{'=' * 80}")
        print(f"Scenario {i}")
        print(f"{'=' * 80}")
        print(f"User: {message}")

        # Process message
        response = await agent.chat(message)

        print(f"\nChiku: {response}\n")

        # Small delay between scenarios
        await asyncio.sleep(1)

    print("=" * 80)
    print("✅ All scenarios completed!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(test_react_agent())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
