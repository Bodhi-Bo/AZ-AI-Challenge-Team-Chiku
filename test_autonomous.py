"""
Test script for the autonomous calendar agent.
Tests complex scenarios like reprioritizing tasks.
"""

import asyncio
import websockets
import json


async def test_autonomous_agent():
    """Test the autonomous agent with various scenarios."""
    user_id = "test_user_autonomous"
    uri = f"ws://localhost:8000/ws/{user_id}"

    print("=" * 80)
    print("Testing Autonomous Calendar Agent")
    print("=" * 80)

    async with websockets.connect(uri) as websocket:
        # Receive welcome message
        welcome = await websocket.recv()
        data = json.loads(welcome)
        print(f"\n✅ Connected: {data['text']}\n")

        # Test scenarios
        # Test scenarios
        scenarios = [
            # Scenario 1: Create some events
            {
                "message": "Create a meeting tomorrow at 2pm for 60 minutes called Team Standup",
                "description": "Create event with all details",
            },
            {
                "message": "Schedule yoga on 2025-11-10 at 9am for 45 minutes",
                "description": "Create another event",
            },
            {
                "message": "Add dentist appointment on 2025-11-10 at 3pm for 30 minutes",
                "description": "Create third event",
            },
            # Scenario 2: View events
            {
                "message": "What events do I have on 2025-11-10?",
                "description": "Get events for a specific date",
            },
            # Scenario 3: Complex reprioritization (the key test!)
            {
                "message": "I'm feeling overwhelmed today. Can you show me what I have scheduled for November 10th and suggest which tasks I could move to November 11th?",
                "description": "Complex: get events + suggest reprioritization",
            },
            # Scenario 4: User confirms the plan
            {
                "message": "Yes, please go ahead and move the yoga session to November 11th",
                "description": "User confirms - agent should execute updates and show final schedule",
            },
            # Scenario 5: Verify the changes
            {
                "message": "Show me my schedule for both November 10th and 11th",
                "description": "Verify events were moved correctly",
            },
            # Scenario 6: Test rejection and alternative
            {
                "message": "Actually, can you move the dentist appointment to November 12th instead?",
                "description": "User requests different change",
            },
            # Scenario 7: Partial confirmation
            {
                "message": "Yes, move the dentist to the 12th",
                "description": "Confirm the dentist move",
            },
            # Scenario 8: Casual chat
            {"message": "Thanks for your help!", "description": "Casual conversation"},
        ]

        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{'=' * 80}")
            print(f"Scenario {i}: {scenario['description']}")
            print(f"{'=' * 80}")
            print(f"User: {scenario['message']}")

            # Send message
            await websocket.send(
                json.dumps({"type": "message", "text": scenario["message"]})
            )

            # Receive response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"\nAssistant: {data['text']}\n")

            # Small delay between scenarios
            await asyncio.sleep(1)

        print("=" * 80)
        print("✅ All scenarios completed!")
        print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(test_autonomous_agent())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure the server is running:")
        print("   uvicorn app.main:app --reload")
