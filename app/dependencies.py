from functools import lru_cache

from app.services.agents.langchain.agent import build_graph
from app.services.agents.langchain.utils.tools import build_tools
from app.services.chat_service import ChatService


@lru_cache(maxsize=1)
def get_langgraph_graph():
    return build_graph(build_tools())


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    """Dependency injector for ChatService"""
    return ChatService(langgraph_graph=get_langgraph_graph())
