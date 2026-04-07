from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.os import AgentOS

from app.services.agents.agno.utils.instructions import EXTRACTION_INSTRUCTIONS
from app.services.agents.agno.utils.schemas import TripState
from app.services.agents.agno.utils.tools import set_trip_info


EXTRACTION_AGENT_NAME = "Trip Extraction Agent"


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


extraction_agent = build_extraction_agent()
agent_os = AgentOS(agents=[extraction_agent])
app = agent_os.get_app()