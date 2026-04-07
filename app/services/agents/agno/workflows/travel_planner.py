from agno.db.in_memory import InMemoryDb
from agno.run import RunContext
from agno.workflow import Router, Step, StepInput, StepOutput, Workflow

from app.services.agents.agno.agents.extraction import extraction_agent
from app.services.agents.agno.agents.follow_up import FOLLOW_UP_AGENT_NAME, follow_up_agent
from app.services.agents.agno.utils.schemas import TripState


PLANNING_STEP_NAME = "Planning Step"


def planning_function(_step_input: StepInput, run_context: RunContext) -> StepOutput:
    trip = TripState.model_validate(run_context.session_state.get("trip", {}))
    return StepOutput(
        content=(
            "Planning is ready for "
            f"city={trip.city}, date={trip.date}, budget={trip.budget}."
        )
    )


def build_planning_step() -> Step:
    return Step(name=PLANNING_STEP_NAME, executor=planning_function)


planning_step = build_planning_step()


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


travel_planner_workflow = Workflow(
    name="Travel Planning Workflow",
    steps=[extraction_agent, planner_route],
    db=InMemoryDb(),
)