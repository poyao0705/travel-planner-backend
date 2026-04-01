from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.run import RunContext
from agno.workflow import Step, StepInput, StepOutput

from app.services.agents.agno.utils.instructions import (
    EXTRACTION_INSTRUCTIONS,
    FOLLOW_UP_INSTRUCTIONS,
)
from app.services.agents.agno.utils.schemas import TripState
from app.services.agents.agno.utils.tools import set_trip_info


EXTRACTION_AGENT_NAME = "Trip Extraction Agent"
FOLLOW_UP_AGENT_NAME = "Follow-up Agent"
PLANNING_STEP_NAME = "Planning Step"


def build_extraction_agent() -> Agent:
    return Agent(
        name=EXTRACTION_AGENT_NAME,
        model=OpenRouter(id="gpt-5.4-mini"),
        instructions=EXTRACTION_INSTRUCTIONS,
        session_state={"trip": TripState().model_dump()},
        tools=[set_trip_info],
        add_datetime_to_context=True,
        add_history_to_context=True,
        add_session_state_to_context=True,
        num_history_runs=3,
        markdown=True,
    )


def build_follow_up_agent() -> Agent:
    return Agent(
        name=FOLLOW_UP_AGENT_NAME,
        model=OpenRouter(id="gpt-5.4-mini"),
        instructions=FOLLOW_UP_INSTRUCTIONS,
        add_session_state_to_context=True,
    )


def planning_function(step_input: StepInput, run_context: RunContext) -> StepOutput:
    trip = TripState.model_validate(run_context.session_state.get("trip", {}))
    return StepOutput(
        content=(
            "Planning is ready for "
            f"city={trip.city}, date={trip.date}, budget={trip.budget}."
        )
    )


def build_planning_step() -> Step:
    return Step(name=PLANNING_STEP_NAME, executor=planning_function)


extraction_agent = build_extraction_agent()
follow_up_agent = build_follow_up_agent()
planning_step = build_planning_step()