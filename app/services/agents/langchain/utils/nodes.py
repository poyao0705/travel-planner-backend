from langchain_core.runnables import RunnableConfig

from app.schemas import DraftTravelPlan
from app.services.agents.langchain.utils.state import (
    # LLMInputState,
    TravelPlannerState,
)


def build_chat_node(model):
    def chat_node(state: TravelPlannerState, config: RunnableConfig):
        response = model.invoke(state["messages"], config=config)
        return {"messages": [response]}

    return chat_node


def build_extraction_node(model):
    def extraction_node(state: TravelPlannerState, config: RunnableConfig):
        structured_model = model.with_structured_output(DraftTravelPlan)
        response = structured_model.invoke(state["messages"], config=config)
        return {"draft_travel_plan": response}

    return extraction_node
