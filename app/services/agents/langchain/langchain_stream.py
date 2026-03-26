import uuid
from typing import Any

from langchain_core.messages import AIMessage, AIMessageChunk

from app.services.agents.stream import StreamEvent, stream_events_to_vercel_sse


def _extract_text_chunks(message: object) -> list[str]:
    """Return text chunks from a LangChain message or message chunk."""
    if not isinstance(message, (AIMessage, AIMessageChunk)):
        return []

    text_chunks: list[str] = []

    content_blocks = getattr(message, "content_blocks", None) or []
    for block in content_blocks:
        if block.get("type") == "text":
            text = block.get("text")
            if isinstance(text, str) and text:
                text_chunks.append(text)

    return text_chunks


def _message_content(message: object) -> str:
    """Best-effort plain text extraction from a LangChain message."""
    content = getattr(message, "content", "")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                text = part.get("text")
                if text:
                    text_parts.append(str(text))
            elif hasattr(part, "text"):
                text = getattr(part, "text", "")
                if text:
                    text_parts.append(str(text))
        return "".join(text_parts)

    return str(content) if content is not None else ""


async def langchain_events_to_internal(events, *, out: dict | None = None):
    """Translate LangGraph astream events into the shared internal stream format."""
    text_part_id = f"text_{uuid.uuid4().hex}"
    text_started = False
    latest_values: Any = None

    async for part in events:
        part_type = part.get("type")

        if part_type == "messages":
            message, _ = part["data"]
            text_chunks = _extract_text_chunks(message)

            if text_chunks:
                if not text_started:
                    yield StreamEvent.text_start(text_part_id)
                    text_started = True
                yield StreamEvent.text_delta(
                    text_part_id,
                    "".join(text_chunks),
                )

        elif part_type == "values":
            latest_values = part["data"]

    if text_started:
        yield StreamEvent.text_end(text_part_id)

    if out is not None:
        out["state"] = latest_values


async def langchain_graph_to_vercel_sse(events, *, out: dict | None = None):
    """Translate LangGraph astream output into Vercel AI SDK SSE strings."""
    async for chunk in stream_events_to_vercel_sse(
        langchain_events_to_internal(events, out=out)
    ):
        yield chunk
