"""
Quick test to verify the decompose_task tool works correctly.
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agent.decomposer_tools import decompose_task
from app.agent.tool_context import set_current_user_id, reset_current_user_id
from app.services.conversation_service import conversation_service


async def test_decompose_task():
    """Test the decompose_task tool with a sample task."""

    # Set up test user
    test_user_id = "test_user_decomposer"
    context_token = set_current_user_id(test_user_id)

    try:
        # Set up some initial state for context extraction
        conversation_service.update_conversation_state(
            test_user_id,
            {
                "intent": {
                    "high_level_goal": "prepare for exam",
                    "current_objective": "study biology",
                    "priority": "high",
                },
                "context": {
                    "emotional_state": "overwhelmed",
                    "time_horizon": "this week",
                    "constraints": ["has class in afternoons"],
                    "preferences": {
                        "best_time_of_day": "morning",
                        "session_length": 25,
                    },
                },
            },
        )

        print("=" * 80)
        print("TEST 1: Auto-extract context from state")
        print("=" * 80)

        # Test 1: Let it extract context from state
        result1 = await decompose_task.ainvoke(
            {
                "task_description": "Study for biology midterm covering chapters 5-8",
                "deadline": "2025-11-21",
            }
        )

        print_result(result1, "AUTO-EXTRACTED CONTEXT")

        print("\n" + "=" * 80)
        print("TEST 2: Explicit context_dict provided")
        print("=" * 80)

        # Test 2: Provide explicit context
        result2 = await decompose_task.ainvoke(
            {
                "task_description": "Write a 5-page research paper on climate change",
                "deadline": "2025-11-20",
                "context_dict": {
                    "user_emotional_state": "anxious",
                    "importance": "high",
                    "task_type": "academic",
                    "time_constraints": {
                        "approx_available_minutes_before_deadline": 300
                    },
                    "preferences": {
                        "preferred_session_length_minutes": 20,
                        "best_time_of_day": "morning",
                    },
                    "known_difficulties": ["task_initiation", "perfectionism"],
                },
            }
        )

        print_result(result2, "EXPLICIT CONTEXT")

        print("\n" + "=" * 80)
        print("TEST 3: Minimal - just task description")
        print("=" * 80)

        # Test 3: Minimal input
        result3 = await decompose_task.ainvoke(
            {"task_description": "Plan a surprise birthday party for my friend"}
        )

        print_result(result3, "MINIMAL INPUT")

    finally:
        reset_current_user_id(context_token)


def print_result(result, test_name):
    """Print the result of a decompose_task call."""
    print(f"\n{test_name} RESULT:")
    print("-" * 80)

    if result.get("success"):
        print("✓ Success!")
        print(f"\nSummary:")
        summary = result.get("summary", {})
        print(f"  Title: {summary.get('title')}")
        print(f"  Total subtasks: {summary.get('total_subtasks')}")
        print(f"  Total time: {summary.get('total_time_minutes')} minutes")
        print(f"  Quick wins: {summary.get('quick_wins_count')}")
        print(f"  Feasibility: {summary.get('plan_feasibility')}")

        if summary.get("time_constraint_note"):
            print(f"  Note: {summary.get('time_constraint_note')}")

        # Show first few subtasks
        breakdown = result.get("breakdown", {})
        subtasks = breakdown.get("subtasks", [])

        print(f"\nFirst 2 subtasks:")
        for i, subtask in enumerate(subtasks[:2], 1):
            print(
                f"\n  {i}. {subtask.get('title')} ({subtask.get('estimated_time_minutes')} min)"
            )
            print(f"     Priority: {subtask.get('priority')}")
            print(f"     Energy: {subtask.get('energy_level')}")
            print(f"     Strategy: {subtask.get('adhd_strategy', 'N/A')[:60]}...")

        print(f"\n✓ Full breakdown contains {len(subtasks)} subtasks")

    else:
        print("✗ Failed!")
        print(f"Error: {result.get('error')}")
        print(f"Message: {result.get('message')}")


if __name__ == "__main__":
    asyncio.run(test_decompose_task())
