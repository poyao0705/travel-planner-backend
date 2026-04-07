from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.os import AgentOS

from app.services.agents.agno.utils.instructions import FOLLOW_UP_INSTRUCTIONS


FOLLOW_UP_AGENT_NAME = "Follow-up Agent"


def build_follow_up_agent() -> Agent:
    return Agent(
        name=FOLLOW_UP_AGENT_NAME,
        model=OpenRouter(id="gpt-5.4-mini"),
        instructions=FOLLOW_UP_INSTRUCTIONS,
        add_session_state_to_context=True,
    )


follow_up_agent = build_follow_up_agent()
agent_os = AgentOS(agents=[follow_up_agent])
app = agent_os.get_app()