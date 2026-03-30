from pydantic import BaseModel, Field

from agno.run import RunContext
from agno.tools import tool

from app.services.agents.agno.utils.schemas import TripState


class TripInput(BaseModel):
    city: str | None = Field(default=None, description="Destination city")
    date: str | None = Field(
        default=None,
        description="Trip date in YYYY-MM-DD format",
    )
    budget: str | None = Field(default=None, description="Budget range")


@tool(stop_after_tool_call=True)
def set_trip_info(run_context: RunContext, trip_input: TripInput) -> str:
    """Store extracted trip details in session state."""
    trip = TripState.model_validate(run_context.session_state.get("trip", {}))

    if trip_input.city is not None:
        trip.city = trip_input.city
    if trip_input.date is not None:
        trip.date = trip_input.date
    if trip_input.budget is not None:
        trip.budget = trip_input.budget

    run_context.session_state["trip"] = trip.model_dump()
    return "Trip information updated."