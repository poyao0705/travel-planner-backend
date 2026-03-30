from pydantic import BaseModel, Field


class TripState(BaseModel):
    city: str | None = Field(
        default=None,
        description="The destination city extracted from the user's messages.",
    )
    date: str | None = Field(
        default=None,
        description="The trip date extracted from the user's messages.",
    )
    budget: str | None = Field(
        default=None,
        description="The budget range extracted from the user's messages.",
    )