# Agent Tools Organization

The agent tools are now organized into logical categories for better maintainability and clarity.

## File Structure

### Core Files
- **`react_agent.py`** - Main ReAct agent implementation with tool orchestration
- **`mega_prompt.txt`** - System prompt template for Chiku persona

### Tool Categories

#### 1. State Management (`state_tools.py`)
Tools for managing conversation state and user profile:
- `update_working_state` - Update transient conversation state (MUST be called first each iteration)
- `update_user_profile` - Update persistent user profile (call before ending conversations)

#### 2. Message Tools (`message_tools.py`)
Tools for communicating with the user:
- `send_interrogative_message` - Ask clarifying questions (continues conversation)
- `send_declarative_message` - Send informative messages (ends conversation)

#### 3. Calendar Query Tools (`calendar_query_tools.py`)
Read-only calendar operations:
- `get_events` - Get events in a date range
- `get_events_on_date` - Get events for a specific date
- `get_todays_schedule` - Get today's events
- `get_tomorrows_schedule` - Get tomorrow's events
- `get_week_schedule` - Get next 7 days of events
- `find_event_by_title` - Search events by title (returns event_id for modifications)

#### 4. Calendar Action Tools (`calendar_action_tools.py`)
Calendar data modifications:
- `create_calendar_event` - Create new event
- `update_calendar_event` - Update existing event (requires event_id)
- `move_event_to_date` - Move event to different date/time (requires event_id)
- `delete_calendar_event` - Delete event (requires event_id)

**Important:** All modification tools require an `event_id` obtained from query tools first.

#### 5. Availability Tools (`availability_tools.py`)
Time slot availability checking:
- `find_available_slots` - Find free time slots on a date
- `check_time_availability` - Check if a specific time is free

#### 6. Reminder Tools (`reminder_tools.py`)
Reminder management:
- `create_reminder` - Create standalone reminder
- `create_reminder_for_event` - Create reminder before an event (requires event_id)
- `get_upcoming_reminders` - Get reminders in next X hours
- `get_pending_reminders` - Get all pending reminders
- `mark_reminder_completed` - Mark reminder as done
- `snooze_reminder` - Delay reminder by X minutes
- `delete_reminder` - Delete reminder

## Legacy Files (Can be deprecated)

- **`tools.py`** - Old tool file, functionality moved to `state_tools.py`
- **`mongo_tools.py`** - Old tool file, functionality moved to category-specific files

## Adding New Tools

When adding new tools:

1. Determine the appropriate category
2. Add the tool to the relevant category file
3. Import it in `react_agent.py` (both in imports and in `self.tools` list)
4. Add it to the `tool_map` in `_execute_tool()` method
5. Update this README

## Tool Call Protocol

All tool usage must follow this protocol:

1. **Every iteration MUST start with `update_working_state`**
2. **Minimum 2 tools per iteration** (state update + action/message tool)
3. **Maximum 7 tools per iteration** (state update + action + 5 preemptive)
4. **Message tools end the interaction** (interrogative continues, declarative resets state)
5. **Update user profile before declarative messages** to persist learnings

## Event ID Requirements

**CRITICAL:** When modifying calendar events or creating event-based reminders:

1. First query to get the event (using `find_event_by_title` or date-based queries)
2. Extract the `event_id` from results (MongoDB ObjectId string like "691317c99da9a2b1525f35c9")
3. Use that exact `event_id` in modification tools

**DO NOT:**
- Use event titles as event_id ❌
- Make up identifier strings ❌
- Guess event_id values ❌
