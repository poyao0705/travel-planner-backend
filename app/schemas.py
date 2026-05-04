from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class MapResult(BaseModel):
    """The response from the map agent, which provides information about coordinates."""

    found: bool = Field(
        ..., description="Whether the location could be resolved reliably"
    )
    query: str = Field(..., description="The location query used for geocoding")
    center: list[float] | None = Field(
        default=None,
        description="The latitude and longitude of the location",
    )
    zoom: int | None = Field(default=None, description="The zoom level for the map")
    display_name: str | None = Field(
        default=None,
        description="The canonical address returned by the geocoder",
    )
    message: str | None = Field(
        default=None,
        description="Why a location could not be resolved, if applicable",
    )


# Plan Schemas

# Draft Plan Schemas

ItineraryItemCategory = Literal[
    "ATTRACTION",
    "RESTAURANT",
    "HOTEL",
    "TRANSPORTATION",
    "ACTIVITY",
    "SHOPPING",
    "OTHER",
]


class DraftTravelPlanItem(BaseModel):
    title: str | None = Field(
        default=None, description="The title of the travel plan item"
    )
    description: str | None = Field(
        default=None, description="The description of the travel plan item"
    )
    location_name: str | None = Field(
        default=None, description="The name of the location"
    )
    start_time: str | None = Field(
        default=None, description="The start time of the travel plan item"
    )
    end_time: str | None = Field(
        default=None, description="The end time of the travel plan item"
    )
    category: ItineraryItemCategory | None = Field(
        default=None,
        description="The category of the travel plan item. The type must be one of the ItineraryItemCategory enum values: ATTRACTION, RESTAURANT, HOTEL, TRANSPORTATION, ACTIVITY, SHOPPING, OTHER",
    )


class DraftTravelPlanDay(BaseModel):
    day: int | None = Field(default=None, description="The day number in the plan")
    date: str | None = Field(default=None, description="The date of the day")
    items: list[DraftTravelPlanItem] = Field(
        default_factory=list,
        description="Travel items for the day. The type is a list of DraftTravelPlanItem objects",
    )


class DraftTravelPlan(BaseModel):
    destination: str | None = Field(
        default=None, description="The destination city or region"
    )
    days: int | None = Field(default=None, description="The number of days in the plan")
    start_date: date | None = Field(
        default=None, description="The start date of the plan"
    )
    end_date: date | None = Field(default=None, description="The end date of the plan")
    interests: list[str] = Field(
        default_factory=list, description="List of interests or activities"
    )
    constraints: list[str] = Field(
        default_factory=list, description="List of constraints or limitations"
    )
    # TODO: Add budget later
    # budget: str | None = None
    itinerary: list[DraftTravelPlanDay] = Field(
        default_factory=list,
        description="The itinerary for the travel plan. The type is a list of DraftTravelPlanDay objects",
    )
