from typing import Any

# from langchain_core.messages import AnyMessage
from langgraph.graph import MessagesState

from app.schemas import DraftTravelPlan


class TravelPlannerState(MessagesState):
    context: dict[str, Any]
    draft_travel_plan: DraftTravelPlan | None


# class LLMInputState(TypedDict):
#     summarized_messages: list[AnyMessage]
#     context: dict[str, Any]
