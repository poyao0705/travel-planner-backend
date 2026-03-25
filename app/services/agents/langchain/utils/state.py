from typing import NotRequired
from typing_extensions import TypedDict

from langchain.agents import AgentState


class UserIntent(TypedDict, total=False):
    """Coordinator-owned trip requirements collected from the user."""

    city: str


class MapResultState(TypedDict, total=False):
    """UI-facing map payload stored in shared state."""

    found: bool
    query: str
    center: list[float] | None
    zoom: int | None
    display_name: str | None
    message: str | None


class TripState(AgentState, total=False):
    """Shared state for the coordinator and destination specialist."""

    user_intent: NotRequired[UserIntent]
    map_result: NotRequired[MapResultState]