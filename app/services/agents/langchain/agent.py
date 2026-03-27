import argparse
from functools import lru_cache
from typing import Literal

from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.services.agents.langchain.utils.nodes import (
    coordinator_validator,
    extraction_node,
    response_node,
)
from app.services.agents.langchain.utils.schema import TripState


CHECKPOINTER = InMemorySaver()
GraphVariant = Literal["stable", "experimental", "langgraph-v2"]
DEFAULT_GRAPH_VARIANT: GraphVariant = "stable"
SUPPORTED_GRAPH_VARIANTS = frozenset({"stable", "experimental", "langgraph-v2"})


def build_graph():
    """Build the LangGraph coordinator for destination intake."""
    graph = StateGraph(TripState)
    graph.add_node("extraction_node", extraction_node)
    graph.add_node("coordinator_validator", coordinator_validator)
    graph.add_node("response_node", response_node)
    graph.add_edge(START, "extraction_node")
    graph.add_edge("extraction_node", "coordinator_validator")
    graph.add_edge("coordinator_validator", "response_node")
    graph.add_edge("response_node", END)
    return graph


def build_stable_graph():
    """Build the stable coordinator graph."""
    return build_graph()


def build_experimental_graph():
    """Build the experimental coordinator graph."""
    return build_graph()


@lru_cache
def get_travel_agent(graph_variant: GraphVariant = DEFAULT_GRAPH_VARIANT):
    """Return the compiled coordinator graph for the requested variant."""
    if graph_variant == "stable":
        return build_stable_graph().compile(checkpointer=CHECKPOINTER)

    if graph_variant in {"experimental", "langgraph-v2"}:
        return build_experimental_graph().compile(checkpointer=CHECKPOINTER)

    raise ValueError(f"Unsupported graph variant: {graph_variant}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a local coordinator graph test.")
    parser.add_argument(
        "message",
        nargs="?",
        default="I want to travel to Taipei next month.",
        help="User message to send into the coordinator graph.",
    )
    parser.add_argument(
        "--thread-id",
        default="local-test-thread",
        help="Checkpoint thread id used by the graph checkpointer.",
    )
    args = parser.parse_args()

    test_graph = get_travel_agent()
    graph_result = test_graph.invoke(
        {"messages": [HumanMessage(content=args.message)]},
        {"configurable": {"thread_id": args.thread_id}},
    )

    latest_reply = ""
    for message in reversed(graph_result.get("messages", [])):
        if getattr(message, "type", "") in {"ai", "assistant"}:
            latest_reply = getattr(message, "content", "")
            break

    print("=== Graph Test Result ===")
    print(f"thread_id: {args.thread_id}")
    print(f"input: {args.message}")
    print(f"city: {graph_result.get('city')}")
    print(f"assistant: {latest_reply}")