from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
import logging
from app.agent.state import AgentState
from app.agent.nodes import (
    classify_intent,
    gather_event_info,
    create_event,
    casual_chat,
)

# Configure logging
logger = logging.getLogger(__name__)


def route_after_classification(state: AgentState) -> str:
    """Route to appropriate node after intent classification."""
    next_action = state.get("next_action")
    logger.info(f"ROUTING after classification: next_action = {next_action}")

    if next_action == "gather_info":
        logger.info("→ Routing to: gather_info")
        return "gather_info"
    elif next_action == "chat":
        logger.info("→ Routing to: chat")
        return "chat"
    else:
        logger.info("→ Routing to: END")
        return END


def route_after_gathering(state: AgentState) -> str:
    """Route after gathering event info."""
    next_action = state.get("next_action")
    logger.info(f"ROUTING after gathering: next_action = {next_action}")

    if next_action == "create_event":
        logger.info("→ Routing to: create_event")
        return "create_event"
    elif next_action == "gather_info":
        # Need more info - will send response and wait for user input
        logger.info("→ Routing to: END (waiting for user input)")
        return END
    else:
        logger.info("→ Routing to: END")
        return END


def create_agent_graph() -> CompiledStateGraph:
    """
    Create the LangGraph state machine for the calendar assistant.

    Flow:
    1. START -> classify_intent
    2. classify_intent -> gather_info (if calendar) OR chat (if casual)
    3. gather_info -> create_event (if all info) OR END (need more info)
    4. create_event -> END
    5. chat -> END
    """
    # Create the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("classify", classify_intent)
    workflow.add_node("gather_info", gather_event_info)
    workflow.add_node("create_event", create_event)
    workflow.add_node("chat", casual_chat)

    # Set entry point
    workflow.set_entry_point("classify")

    # Add conditional edges from classify
    workflow.add_conditional_edges(
        "classify",
        route_after_classification,
        {"gather_info": "gather_info", "chat": "chat", END: END},
    )

    # Add conditional edges from gather_info
    workflow.add_conditional_edges(
        "gather_info", route_after_gathering, {"create_event": "create_event", END: END}
    )

    # Add edges to END
    workflow.add_edge("create_event", END)
    workflow.add_edge("chat", END)

    # Compile and return
    return workflow.compile()
