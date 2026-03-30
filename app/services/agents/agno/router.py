from agno.workflow import Router, StepInput

from app.services.agents.agno.utils.schemas import TripState
from app.services.agents.agno.steps import (
    FOLLOW_UP_AGENT_NAME,
    PLANNING_STEP_NAME,
    follow_up_agent,
    planning_step,
)


def route_by_trip_state(_step_input: StepInput, session_state: dict) -> str:
    trip = TripState.model_validate(session_state.get("trip", {}))

    if not trip.city or not trip.date or not trip.budget:
        return FOLLOW_UP_AGENT_NAME

    return PLANNING_STEP_NAME


planner_route = Router(
    name="Planner Routing",
    selector=route_by_trip_state,
    choices=[follow_up_agent, planning_step],
)