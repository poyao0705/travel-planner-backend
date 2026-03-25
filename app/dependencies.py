from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from fastapi import Depends

import app.services.agents.adk.adk_agent as adk_agent
from app.services.chat_service import ChatService


# In-memory session service must be global to persist sessions across requests
_session_service = InMemorySessionService()


def get_root_agent():
    return adk_agent.root_agent


def get_session_service():
    return _session_service


def get_runner(
    session_service=Depends(get_session_service),
    root_agent=Depends(get_root_agent),
):
    return Runner(
        agent=root_agent,
        app_name="travel_planner",
        session_service=session_service,
    )


def get_chat_service(
    session_service=Depends(get_session_service),
    runner=Depends(get_runner),
) -> ChatService:
    """Dependency injector for ChatService"""
    return ChatService(session_service, runner)
