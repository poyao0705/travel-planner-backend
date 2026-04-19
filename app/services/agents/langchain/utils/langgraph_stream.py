from typing import Any, AsyncIterable

from app.services.agents.stream import StreamEvent


def _extract_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
        return "".join(parts)
    return ""


async def langgraph_events_to_internal(
    events: AsyncIterable[tuple[Any, dict[str, Any]]],
    *,
    part_id: str,
):
    """Convert LangGraph ``stream_mode="messages"`` events to internal stream events.

    Emits a single text block: ``text-start`` -> N ``text-delta`` -> ``text-end``.
    """
    started = False

    async for chunk, _metadata in events:
        # Only stream assistant-produced token chunks.
        chunk_type = getattr(chunk, "type", None)
        if chunk_type and chunk_type not in ("AIMessageChunk", "ai"):
            continue

        text = _extract_text(getattr(chunk, "content", None))
        if not text:
            continue

        if not started:
            yield StreamEvent.text_start(part_id)
            started = True

        yield StreamEvent.text_delta(part_id, text)

    if started:
        yield StreamEvent.text_end(part_id)
