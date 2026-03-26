import argparse
from functools import lru_cache
from operator import add
from typing import Literal

from langchain.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from typing_extensions import Annotated

from app.core.llm import get_extractor_llm, get_stream_llm
from app.services.agents.langchain.utils.prompt import COORDINATOR_PROMPT_V0


CHECKPOINTER = InMemorySaver()
GraphVariant = Literal["stable", "experimental", "langgraph-v2"]
DEFAULT_GRAPH_VARIANT: GraphVariant = "stable"
SUPPORTED_GRAPH_VARIANTS = frozenset({"stable", "experimental", "langgraph-v2"})


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


class CityExtraction(BaseModel):
    city: str | None = Field(
        default=None,
        description="The destination city extracted from the latest user message, or null if not found.",
    )


def _get_latest_user_message_text(messages: list[AnyMessage]) -> str:
    for chat_message in reversed(messages):
        if isinstance(chat_message, HumanMessage):
            content = getattr(chat_message, "content", "")
            if isinstance(content, str):
                return content
    return ""


def extraction_node(state: TripState) -> TripState:
    latest_user_message = _get_latest_user_message_text(state.messages)
    if not latest_user_message:
        return {}

    extractor_llm = get_extractor_llm().with_structured_output(CityExtraction)

    extraction_prompt = """
Extract the destination city from the latest user message.

Rules:
- Only extract. Do not generate, rewrite, or infer extra details.
- Return city = null if no destination city is present.
- Return city = null for countries, regions, islands, states, provinces, or broad destinations.
- Valid output must be a real city name only.

Examples:
- "I want to travel to Taipei next month." -> city = "Taipei"
- "Plan me a trip to Taiwan." -> city = null
- "I want to visit Japan." -> city = null
"""

    result = extractor_llm.invoke(
        [
            SystemMessage(content=extraction_prompt),
            HumanMessage(content=latest_user_message),
        ]
    )

    if not result.city:
        return {}

    return {"city": result.city}


def coordinator_validator(state: TripState) -> TripState:
    """Validate that the coordinator extracted a city, and if not, prompt for clarification."""
    missing = []
    if not state.city:
        missing.append(MissingField(field="city", reason="Needed to plan itinerary."))

    return {
        "ready_to_plan": len(missing) == 0,
        "missing_field": missing,
    }


def response_node(state: TripState) -> TripState:
    missing = state.missing_field or []

    # -----------------------------
    # STREAMING LLM (UX)
    # -----------------------------
    system_prompt = COORDINATOR_PROMPT_V0

    if state.city:
        system_prompt += f"""

Known destination city: {state.city}
Confirm the city and continue the planning conversation without asking for the destination again.
"""

    if missing:
        system_prompt += f"""
Missing required fields: {missing}
Ask ONLY for missing fields.
"""

    stream_llm = get_stream_llm()

    stream = stream_llm.stream(
        [SystemMessage(content=system_prompt)] + state.messages
    )

    full_reply = ""
    for chunk in stream:
        token = getattr(chunk, "content", "")
        full_reply += token

    return {"messages": [AIMessage(content=full_reply)]}


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
