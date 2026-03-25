from pydantic import BaseModel, Field as PydanticField
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from app.core.llm import get_root_llm
from app.services.agents.langchain.utils.prompt import COORDINATOR_PROMPT
from app.services.agents.langchain.utils.schemas import MapResult
from app.services.agents.langchain.utils.state import TripState
from app.services.agents.langchain.utils.tools import geocode_location


_CHECKPOINTER = InMemorySaver()


# ── structured output schema for the coordinator LLM ──────────────────────────

class _CityExtraction(BaseModel):
    destination_city: str | None = PydanticField(
        default=None,
        description=(
            "The destination city extracted from the user's message, "
            "or null if the user has not specified one."
        ),
    )
    reply: str = PydanticField(
        description=(
            "A short confirmation if a destination was found, "
            "or a clarification question if the destination is still unknown."
        ),
    )


# ── graph nodes ────────────────────────────────────────────────────────────────

def coordinator_node(state: TripState) -> Command:
    """Extract destination city from the conversation and route accordingly."""
    llm = get_root_llm().with_structured_output(_CityExtraction)
    extraction: _CityExtraction = llm.invoke(
        [SystemMessage(content=COORDINATOR_PROMPT)] + state["messages"]
    )

    if extraction.destination_city:
        return Command(
            update={
                "user_intent": {"city": extraction.destination_city.strip()},
                "messages": [AIMessage(content=extraction.reply)],
            },
            goto="geocode",
        )

    return Command(
        update={"messages": [AIMessage(content=extraction.reply)]},
        goto=END,
    )


def geocode_node(state: TripState) -> dict:
    """Resolve the destination city to map coordinates and persist to state."""
    city = (state.get("user_intent") or {}).get("city", "").strip()
    if not city:
        return {}

    raw: dict = geocode_location.invoke({"location": city})

    lat = raw.get("latitude")
    lon = raw.get("longitude")
    display_name: str | None = raw.get("display_name")

    # Derive a canonical city name from the geocoder display name.
    canonical = (
        display_name.split(",")[0].strip()
        if display_name
        else city
    )

    map_result = MapResult(
        found=raw.get("found", False),
        query=raw.get("query", city),
        center=[lat, lon] if lat is not None and lon is not None else None,
        zoom=raw.get("zoom"),
        display_name=display_name,
        message=raw.get("message"),
    )

    return {
        "user_intent": {"city": canonical},
        "map_result": map_result.model_dump(),
    }


# ── graph compilation ──────────────────────────────────────────────────────────

def _build_graph():
    graph = StateGraph(TripState)
    graph.add_node("coordinator", coordinator_node)
    graph.add_node("geocode", geocode_node)
    graph.add_edge(START, "coordinator")
    graph.add_edge("geocode", END)
    return graph.compile(checkpointer=_CHECKPOINTER)


_graph = _build_graph()


def get_coordinator_agent():
    """Return the compiled coordinator graph."""
    return _graph


def invoke_coordinator(
    message: str,
    thread_id: str,
    state: TripState | None = None,
) -> TripState:
    """Run the coordinator with thread-scoped checkpoint persistence."""
    state_input: TripState = {
        "messages": [{"role": "user", "content": message}],
    }
    if state:
        state_input.update(state)
        state_input["messages"] = [{"role": "user", "content": message}]

    result = _graph.invoke(
        state_input,
        {"configurable": {"thread_id": thread_id}},
    )
    output: TripState = {"messages": result["messages"]}
    if "user_intent" in result:
        output["user_intent"] = result["user_intent"]
    if "map_result" in result:
        output["map_result"] = result["map_result"]
    return output

