"""
Action tools for the Decomposer Agent.

These tools enable the decomposer to signal its intent:
- ask_for_more_information: Request clarification from the user (supports batch questions)
- submit_final_plan: Submit the completed task breakdown
"""

from langchain_core.tools import tool
import logging
from typing import Dict, Any, List, Union, Optional

# Configure logging
logger = logging.getLogger(__name__)


@tool
def ask_for_more_information(
    questions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Ask the main agent/user for clarification about the task.

    **Ask ALL questions you need to create an excellent plan!**
    The main agent will collect all answers before calling you again.

    **When to use:**
    - Task scope is vague (e.g., "study for exam" without topics/chapters specified)
    - You don't know the user's starting point (starting from scratch? have notes already?)
    - Time available is unclear or seems insufficient for the described work
    - Resources are unknown (do they have textbook? online access? class notes?)
    - You recognize specific content (e.g., "Campbell Biology") but don't know which chapters
    - The task is large but you don't know what subset to focus on
    - Deadline is missing or unclear

    **Format - always a list (even for single question):**
    questions = [
        {
            "question": "Which chapters or topics will your exam cover?",
            "verification": "non_empty",  # Required: non-empty answer
            "hint": "Please list the specific chapters or topics (e.g., 'Chapters 1-3' or 'Cell biology and genetics')"
        },
        {
            "question": "When is this due? (date and time if known)",
            "verification": "optional",  # User can skip
            "hint": "Answer like 'November 20 at 2pm' or 'next Tuesday' or say 'not sure' to skip"
        },
        {
            "question": "Are you starting from scratch, or do you already have notes/materials prepared?",
            "verification": "choice:from_scratch|have_notes|partially_prepared",
            "hint": "Please answer: 'from scratch', 'have notes', or 'partially prepared'"
        },
        {
            "question": "Roughly how much time do you have available to work on this?",
            "verification": "optional",  # User can skip
            "hint": "You can answer in hours (e.g., '3 hours') or say 'not sure' to skip"
        }
    ]

    **Verification types:**
    - "non_empty": Answer must not be empty/whitespace
    - "yes_no": Must be yes/no/maybe
    - "choice:option1|option2|option3": Must match one of the choices (case-insensitive)
    - "number": Must contain a number
    - "optional": User can skip (say "skip", "don't know", etc.)
    - "regex:pattern": Custom regex pattern (use sparingly)

    **Best practices:**
    - Be thorough: ask ALL questions needed to create a great plan (typically 2-5 questions)
    - If deadline is missing, include it as an optional question
    - Use "optional" for nice-to-have info
    - Provide helpful hints that show example answers
    - Order from most to least important

    Args:
        questions: List of question objects. Each question object should have:
                  - question: str (the question text)
                  - verification: str (verification type/pattern)
                  - hint: str (optional, shown if user gives invalid answer)

    Returns:
        dict: Signal that questions need answers. Main agent will collect all answers
              and call you back with the full conversation_history.
              Format: {"questions": [...], "awaiting_responses": True}
    """
    if not isinstance(questions, list):
        logger.error(
            f"[DECOMPOSER] Invalid questions format: {type(questions)}. Must be a list."
        )
        # Convert to list format
        questions = [
            {"question": str(questions), "verification": "non_empty", "hint": ""}
        ]

    logger.info(
        f"[DECOMPOSER] Asking batch of {len(questions)} question(s) (cost-optimized)"
    )
    for i, q in enumerate(questions, 1):
        logger.info(f"  Q{i}: {q.get('question', '???')[:60]}...")

    return {
        "questions": questions,
        "awaiting_responses": True,
    }


@tool
def submit_final_plan(
    main_task: Dict[str, Any],
    subtasks: List[Dict[str, Any]],
    quick_wins: Optional[List[str]] = None,
    high_focus_tasks: Optional[List[str]] = None,
    low_energy_tasks: Optional[List[str]] = None,
    suggested_breaks: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Submit the final task breakdown plan.

    **Only call this when:**
    - You have enough information to create detailed, specific, actionable subtasks
    - You can provide concrete steps (not vague placeholders like "study chapter 1")
    - Time constraints are clear enough to prioritize appropriately
    - You've asked clarifying questions if needed and have sufficient answers

    **Call this tool by passing fields directly as arguments:**
    submit_final_plan(
      main_task={
        "title": "Clear, concise title of the main task",
        "description": "Brief description including any scope limits",
        "total_estimated_time_minutes": 150,
        "constrained_time_minutes": 0,
        "core_subset_minutes": 0,
        "overall_complexity": "low|medium|high",
        "energy_required": "low|medium|high",
        "best_time_of_day": "morning|afternoon|evening|flexible",
        "plan_feasibility": "realistic|time_constrained|severely_time_constrained",
        "time_constraint_note": "Optional explanation if time is tight"
      },
      subtasks=[
        {
          "id": "task_1",
          "title": "Action verb + specific task (< 60 chars)",
          "description": "Detailed step-by-step instructions for someone tired/overwhelmed",
          "estimated_time_minutes": 15,
          "complexity": "low|medium|high",
          "energy_level": "low|medium|high",
          "dependencies": [],
          "prerequisites": ["items needed before starting"],
          "skills_required": ["email", "writing"],
          "adhd_strategy": "Specific strategy for this task",
          "reward_after": "Small immediate reward",
          "transition_time_minutes": 5,
          "can_be_body_doubled": true,
          "order": 1,
          "priority": "essential|helpful_extra|stretch_option"
        }
      ],
      quick_wins=["task_1", "task_3"],
      high_focus_tasks=["task_2"],
      low_energy_tasks=["task_4"],
      suggested_breaks=[
        {
          "after_task": "task_2",
          "duration_minutes": 10,
          "type": "movement|snack|mindfulness|social"
        }
      ]
    )

    **Critical requirements:**
    - Every subtask ≤ 30 minutes (prefer 10-20 min)
    - Titles start with action verbs (Review, Draft, Create, Practice...)
    - Descriptions are concrete and specific, using world knowledge when available
    - At least 1 quick win task identified
    - Priority marking: "essential" tasks must fit within available time

    Args:
        main_task: Main task metadata with title, description, time estimates, complexity
        subtasks: List of subtask objects (at least 1 required)
        quick_wins: List of task IDs for short, easy, rewarding tasks (optional)
        high_focus_tasks: List of task IDs needing peak focus time (optional)
        low_energy_tasks: List of task IDs good for tired/low motivation (optional)
        suggested_breaks: List of break objects with timing and type (optional)

    Returns:
        dict: The final plan ready for the main agent to schedule.
              Format: {"type": "final_plan", "breakdown": {...}, "ready": True}
    """
    # Assemble breakdown from individual arguments
    breakdown = {
        "main_task": main_task,
        "subtasks": subtasks,
        "quick_wins": quick_wins or [],
        "high_focus_tasks": high_focus_tasks or [],
        "low_energy_tasks": low_energy_tasks or [],
        "suggested_breaks": suggested_breaks or [],
    }

    logger.info(
        f"[DECOMPOSER] Submitting final plan: {main_task.get('title', 'Untitled')}"
    )
    logger.debug(f"Plan details: {len(subtasks)} subtasks")
    return {"type": "final_plan", "breakdown": breakdown, "ready": True}
