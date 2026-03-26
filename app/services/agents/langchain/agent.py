import argparse
from operator import add

from langchain.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from typing_extensions import Annotated

from app.core.llm import get_root_llm
from app.services.agents.langchain.utils.prompt import COORDINATOR_PROMPT_V0


CHECKPOINTER = InMemorySaver()


class MissingField(BaseModel):
    field: str
    reason: str


class TripState(BaseModel):
    messages: Annotated[list[AnyMessage], add] = Field(
        default_factory=list,
        description="The conversation history as a list of messages.",
    )
    city: str | None = Field(
        default=None,
        description="The destination city extracted from the user's messages.",
    )
    ready_to_plan: bool = Field(
        default=False,
        description="Whether the coordinator has successfully extracted a destination city and the agent is ready to proceed.",
    )
    missing_field: list[MissingField] = Field(
        default_factory=list,
        description="List of missing fields needed to proceed, if any.",
    )


class CoordinatorOutput(BaseModel):
    reply: str
    city: str | None = Field(
        default=None,
        description="The destination city extracted from the user's messages, or null if not found.",
    )


def coordinator_node(state: TripState) -> TripState:
    """Extract destination city from the conversation and route accordingly."""
    missing = state.missing_field or []

    system_prompt = COORDINATOR_PROMPT_V0

    if missing:
        system_prompt += f"""
    Missing required fields: {missing}

    Ask a follow-up question to collect ONLY the missing fields.
    Do not ask about fields that are already provided.
    """

    llm = get_root_llm().with_structured_output(CoordinatorOutput)
    result = llm.invoke(
        [SystemMessage(content=system_prompt)] + state.messages
    )
    update = {
        "messages": [AIMessage(content=result.reply)]
    }

    if result.city:
        update["city"] = result.city

    return update


def coordinator_validator(state: TripState) -> TripState:
    """Validate that the coordinator extracted a city, and if not, prompt for clarification."""
    missing = []
    if not state.city:
        missing.append(MissingField(field="city", reason="Needed to plan itinerary."))

    return {
        "ready_to_plan": len(missing) == 0,
        "missing_field": missing,
    }

def coordinator_router(_state: TripState) -> str:
    """End the current turn after validation and resume on the next user message."""
    return END


def build_graph():
    """Build the LangGraph coordinator for destination intake."""
    graph = StateGraph(TripState)
    graph.add_node("coordinator_node", coordinator_node)
    graph.add_node("coordinator_validator", coordinator_validator)
    graph.add_edge(START, "coordinator_node")
    graph.add_edge("coordinator_node", "coordinator_validator")
    graph.add_conditional_edges("coordinator_validator", coordinator_router)
    return graph


def get_travel_agent():
    """Return the compiled coordinator graph."""
    return build_graph().compile(checkpointer=CHECKPOINTER)


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
