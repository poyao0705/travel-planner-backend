from functools import lru_cache
from langchain_openrouter import ChatOpenRouter


@lru_cache
def get_root_llm() -> ChatOpenRouter:
    """Initializes and returns the root language model for the agent workflow."""
    return ChatOpenRouter(
        model="anthropic/claude-sonnet-4.5",
        max_completion_tokens=16384,
        # reasoning={"effort": "high"},
    )

def get_map_agent_llm() -> ChatOpenRouter:
    """Initializes and returns the language model for the map agent."""
    return ChatOpenRouter(
        model="anthropic/claude-sonnet-4.5",
        max_completion_tokens=8192,
        # reasoning={"effort": "medium"},
    )
