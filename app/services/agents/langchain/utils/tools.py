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


# @tool
# def geocode_location(location: str) -> dict:
#     """Geocode a destination city and return a map payload."""

#     result = geocode_destination_city(location)
#     data = result.model_dump()
#     center = data.pop("center", None)
#     data["latitude"] = center[0] if center else None
#     data["longitude"] = center[1] if center else None
#     return data

@tool
def geocode_location(location: str) -> dict:
    """Geocode a destination city and return a map payload."""
    result_obj = GEOCODER.geocode(location)

    result = {
        "found": result_obj is not None,
        "query": location,
        "latitude": result_obj.latitude if result_obj else None,
        "longitude": result_obj.longitude if result_obj else None,
        "display_name": result_obj.address if result_obj else None,
    }
    return result
