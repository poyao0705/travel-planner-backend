from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim
from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.genai import types

from app.schemas import MapResult


DEFAULT_MAP_ZOOM = 12
_GEOCODER = Nominatim(user_agent="travel_planner_backend", timeout=10)


# 1. Define your geocoding tool
def geocode_location(query: str) -> dict:
    """Resolve a place name into coordinates using Nominatim."""
    normalized_query = query.strip()
    if not normalized_query:
        return {
            "found": False,
            "query": "",
            "center": None,
            "zoom": None,
            "display_name": None,
            "message": "A place name is required for geocoding.",
        }

    try:
        location = _GEOCODER.geocode(normalized_query)
    except (GeocoderTimedOut, GeocoderServiceError, ValueError) as exc:
        return {
            "found": False,
            "query": normalized_query,
            "center": None,
            "zoom": None,
            "display_name": None,
            "message": f"Geocoding failed: {exc}",
        }

    if location is None:
        return {
            "found": False,
            "query": normalized_query,
            "center": None,
            "zoom": None,
            "display_name": None,
            "message": "No reliable coordinate match was found for that place.",
        }

    return {
        "found": True,
        "query": normalized_query,
        "center": [location.latitude, location.longitude],
        "zoom": DEFAULT_MAP_ZOOM,
        "display_name": location.address,
        "message": None,
    }

map_agent = LlmAgent(
    name="map_agent",
    mode="single_turn",
    model="gemini-2.5-flash",
    description="An agent that provides information about places and coordinates.",
    instruction="""You are a helpful assistant that provides information about places and coordinates.
    You MUST return valid JSON only. Do not include any explanation or text outside JSON.
    If the root agent delegates a question about a place or its location to you,
    ALWAYS call the `geocode_location` tool before responding.
    Never invent or estimate coordinates.
    If the tool returns `found=false`, return JSON matching MapResult with the tool's query and message,
    and set `center` and `zoom` to null.
    If the tool returns `found=true`, return JSON matching MapResult using the tool output exactly.""",
    tools=[geocode_location],
    output_key="map_result",
    output_schema=MapResult,
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=1000,
        ),
    ),
)

# 2. Build the Agent
root_agent = LlmAgent(
    name="search_bot",
    model="gemini-2.5-flash",
    description="A travel agent delegating tasks to subagents to help users plan trips.",
    instruction="""You are a travel agent that plans trips.
    Always ask about the user's travel preferences, proceed only when narrow down to a specific city or location.
    Your job is to provide recommendations for attractions, and itineraries based on user preferences.
    You have to give information about the coordinate of the place user is interested in, and use the map_agent to find this information.
    Do not guess coordinates yourself; delegate coordinate lookups to map_agent.""",
    sub_agents=[map_agent],
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=1000,
        ),
    ),
)
