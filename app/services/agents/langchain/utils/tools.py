from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim
from langchain.tools import tool

from app.services.agents.langchain.utils.schemas import MapResult


DEFAULT_MAP_ZOOM = 12
GEOCODER = Nominatim(user_agent="travel_planner_backend", timeout=10)


def geocode_destination_city(city: str) -> MapResult:
    """Resolve a destination city into map coordinates using Nominatim."""

    normalized_city = city.strip()
    if not normalized_city:
        return MapResult(
            found=False,
            query="",
            center=None,
            zoom=None,
            display_name=None,
            message="A destination city is required before geocoding.",
        )

    try:
        location = GEOCODER.geocode(normalized_city)
    except (GeocoderTimedOut, GeocoderServiceError, ValueError) as exc:
        return MapResult(
            found=False,
            query=normalized_city,
            center=None,
            zoom=None,
            display_name=None,
            message=f"Geocoding failed: {exc}",
        )

    if location is None:
        return MapResult(
            found=False,
            query=normalized_city,
            center=None,
            zoom=None,
            display_name=None,
            message="No reliable coordinate match was found for that destination.",
        )

    return MapResult(
        found=True,
        query=normalized_city,
        center=[location.latitude, location.longitude],
        zoom=DEFAULT_MAP_ZOOM,
        display_name=location.address,
        message=None,
    )


@tool
def geocode_location(location: str) -> dict:
    """Geocode a destination city and return a map payload."""
    result_obj = geocode_destination_city(location)
    center = result_obj.center
    result = {
        "found": result_obj.found,
        "query": result_obj.query,
        "latitude": center[0] if center else None,
        "longitude": center[1] if center else None,
        "display_name": result_obj.display_name,
    }
    return result
