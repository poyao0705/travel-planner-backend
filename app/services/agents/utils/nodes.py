from langchain.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage

from app.core.llm import get_extractor_llm, get_stream_llm
from app.services.agents.utils.prompt import COORDINATOR_PROMPT_V0
from app.services.agents.utils.schema import (
    CityExtraction,
    MissingField,
    TripState,
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
    stream = stream_llm.stream([SystemMessage(content=system_prompt)] + state.messages)

    full_reply = ""
    for chunk in stream:
        token = getattr(chunk, "content", "")
        full_reply += token

    return {"messages": [AIMessage(content=full_reply)]}