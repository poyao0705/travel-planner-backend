from pydantic import BaseModel, Field

class MapResult(BaseModel):
    """The response from the map agent, which provides information about coordinates."""
    found: bool = Field(..., description="Whether the location could be resolved reliably")
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