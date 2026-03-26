from operator import add

from langchain.messages import AnyMessage
from pydantic import BaseModel, Field
from typing_extensions import Annotated


class MissingField(BaseModel):
    field: str
    reason: str


class TripState(BaseModel):
    messages: Annotated[list[AnyMessage], add] = Field(
        default_factory=list,
        description="The conversation history as a list of messages.",
    )
    city: str | None = Field(
        default=None,
        description="The destination city extracted from the user's messages.",
    )
    ready_to_plan: bool = Field(
        default=False,
        description="Whether the coordinator has successfully extracted a destination city and the agent is ready to proceed.",
    )
    missing_field: list[MissingField] = Field(
        default_factory=list,
        description="List of missing fields needed to proceed, if any.",
    )


class CityExtraction(BaseModel):
    city: str | None = Field(
        default=None,
        description="The destination city extracted from the latest user message, or null if not found.",
    )