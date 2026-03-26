import argparse
from operator import add

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from typing_extensions import Annotated
from langchain.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
# from langgraph.types import Command

from app.core.llm import get_root_llm
from app.services.agents.langchain.utils.prompt import COORDINATOR_PROMPT_V0
# from app.services.agents.langchain.utils.schemas import MapResult
# from app.services.agents.langchain.utils.state import TripState


CHECKPOINTER = InMemorySaver()

class MissingField(BaseModel):
    field: str
    reason: str

# class MapResult(BaseModel):
#     found: bool
#     query: str
#     center: list[float] | None = Field(default_factory=list, description="Latitude and longitude coordinates for map centering.")
#     zoom: int = Field(default=12)

class TripState(BaseModel):
    messages: Annotated[list[AnyMessage], add] = Field(default_factory=list, description="The conversation history as a list of messages.")
    city: str | None = Field(default=None, description="The destination city extracted from the user's messages.")
    ready_to_plan: bool = Field(default=False, description="Whether the coordinator has successfully extracted a destination city and the agent is ready to proceed.")
    missing_field: list[MissingField] = Field(default_factory=list, description="List of missing fields needed to proceed, if any.")

class CoordinatorOutput(BaseModel):
    reply: str
    city: str | None = Field(default=None, description="The destination city extracted from the user's messages, or null if not found.")



# # ── structured output schema for the coordinator LLM ──────────────────────────

# class _CityExtraction(BaseModel):
#     destination_city: str | None = PydanticField(
#         default=None,
#         description=(
#             "The destination city extracted from the user's message, "
#             "or null if the user has not specified one."
#         ),
#     )
#     reply: str = PydanticField(
#         description=(
#             "A short confirmation if a destination was found, "
#             "Include thought process reasoning if no destination was found, and ask for clarification if needed. This will be shown to the user as the assistant's response, "
#             "or a clarification question if the destination is still unknown."
#         ),
#     )


# # ── graph nodes ────────────────────────────────────────────────────────────────

# def coordinator_node(state: TripState) -> Command:
#     """Extract destination city from the conversation and route accordingly."""
#     llm = get_root_llm().with_structured_output(_CityExtraction)
#     extraction: _CityExtraction = llm.invoke(
#         [SystemMessage(content=COORDINATOR_PROMPT)] + state["messages"]
#     )

#     if extraction.destination_city:
#         return Command(
#             update={
#                 "user_intent": {"city": extraction.destination_city.strip()},
#                 "messages": [AIMessage(content=extraction.reply)],
#             },
#             goto="geocode",
#         )

#     return Command(
#         update={"messages": [AIMessage(content=extraction.reply)]},
#         goto=END,
#     )


# def geocode_node(state: TripState) -> dict:
#     """Resolve the destination city to map coordinates and persist to state."""
#     city = (state.get("user_intent") or {}).get("city", "").strip()
#     if not city:
#         return {}

#     raw: dict = geocode_location.invoke({"location": city})

#     lat = raw.get("latitude")
#     lon = raw.get("longitude")
#     display_name: str | None = raw.get("display_name")

#     # Derive a canonical city name from the geocoder display name.
#     canonical = (
#         display_name.split(",")[0].strip()
#         if display_name
#         else city
#     )

#     map_result = MapResult(
#         found=raw.get("found", False),
#         query=raw.get("query", city),
#         center=[lat, lon] if lat is not None and lon is not None else None,
#         zoom=raw.get("zoom"),
#         display_name=display_name,
#         message=raw.get("message"),
#     )

#     return {
#         "user_intent": {"city": canonical},
#         "map_result": map_result.model_dump(),
#     }


# # ── graph compilation ──────────────────────────────────────────────────────────

# def _build_graph():
#     graph = StateGraph(TripState)
#     graph.add_node("coordinator", coordinator_node)
#     graph.add_node("geocode", geocode_node)
#     graph.add_edge(START, "coordinator")
#     graph.add_edge("geocode", END)
#     return graph.compile(checkpointer=_CHECKPOINTER)


# _graph = _build_graph()


# def get_coordinator_agent():
#     """Return the compiled coordinator graph."""
#     return _graph


# def invoke_coordinator(
#     message: str,
#     thread_id: str,
#     state: TripState | None = None,
# ) -> TripState:
#     """Run the coordinator with thread-scoped checkpoint persistence."""
#     state_input: TripState = {
#         "messages": [{"role": "user", "content": message}],
#     }
#     if state:
#         state_input.update(state)
#         state_input["messages"] = [{"role": "user", "content": message}]

#     result = _graph.invoke(
#         state_input,
#         {"configurable": {"thread_id": thread_id}},
#     )
#     output: TripState = {"messages": result["messages"]}
#     if "user_intent" in result:
#         output["user_intent"] = result["user_intent"]
#     if "map_result" in result:
#         output["map_result"] = result["map_result"]
#     return output

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

# def geocode_node(state: TripState) -> dict:
#     """Resolve the destination city to map coordinates and persist to state."""
#     city = state.city.strip() if state.city else ""
#     if not city:
#         return {}

#     raw: dict = geocode_location.invoke({"location": city})

#     lat = raw.get("latitude")
#     lon = raw.get("longitude")
#     display_name: str | None = raw.get("display_name")

#     # Derive a canonical city name from the geocoder display name.
#     canonical = (
#         display_name.split(",")[0].strip()
#         if display_name
#         else city
#     )

#     map_result = MapResult(
#         found=raw.get("found", False),
#         query=raw.get("query", city),
#         center=[lat, lon] if lat is not None and lon is not None else None,
#         zoom=raw.get("zoom"),
#         display_name=display_name,
#         message=raw.get("message"),
#     )

#     return {
#         "map_result": map_result.model_dump(),
#     }

def coordinator_router(_state: TripState) -> str:
    """End the current turn after validation and resume on the next user message."""
    return END

def build_graph():
    """Placeholder for future graph-based implementation."""
    graph = StateGraph(TripState)
    # graph.add_node("coordinator", coordinator_node)
    # graph.add_node("geocode", geocode_node)
    graph.add_node("coordinator_node", coordinator_node)
    graph.add_node("coordinator_validator", coordinator_validator)
    graph.add_edge(START, "coordinator_node")
    graph.add_edge("coordinator_node", "coordinator_validator")
    graph.add_conditional_edges("coordinator_validator", coordinator_router)
    # graph.add_edge("coordinator_node", END)
    # graph.add_edge("geocode", END)
    return graph



def get_travel_agent():
    """Return the compiled coordinator graph."""
    # Placeholder for future graph-based implementation
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
