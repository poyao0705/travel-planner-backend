import os
from functools import lru_cache
from langchain_openrouter import ChatOpenRouter


def _build_llm(model: str, *, max_completion_tokens: int) -> ChatOpenRouter:
    return ChatOpenRouter(
        model=model,
        max_completion_tokens=max_completion_tokens,
    )


@lru_cache
def get_stream_llm() -> ChatOpenRouter:
    """Initializes and returns the streaming language model for user-facing replies."""
    return _build_llm(
        model=os.getenv("STREAM_LLM_MODEL", "anthropic/claude-sonnet-4.5"),
        max_completion_tokens=16384,
    )


@lru_cache
def get_extractor_llm() -> ChatOpenRouter:
    """Initializes and returns the extractor model for lightweight structured parsing."""
    return _build_llm(
        model=os.getenv("EXTRACTOR_LLM_MODEL", "anthropic/claude-3.5-haiku"),
        max_completion_tokens=512,
    )


@lru_cache
def get_root_llm() -> ChatOpenRouter:
    """Backward-compatible alias for the default streaming language model."""
    return get_stream_llm()

@lru_cache
def get_map_agent_llm() -> ChatOpenRouter:
    """Initializes and returns the language model for the map agent."""
    return _build_llm(
        model=os.getenv("MAP_AGENT_LLM_MODEL", "anthropic/claude-sonnet-4.5"),
        max_completion_tokens=8192,
    )
