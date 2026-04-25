from typing import Any, AsyncIterator

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
    events: AsyncIterator,
    *,
    part_id: str,
):
    """Convert LangGraph ``stream_mode="messages"`` events to internal stream events.

    Emits a single text block: ``text-start`` -> N ``text-delta`` -> ``text-end``.
    """
    started = False

    # Refactor to version 2 of langgraph streaming API
    async for part in events:
        if part["type"] == "messages":
            msg, _ = part["data"]
            #
            content = _extract_text(getattr(msg, "content", None))
            # Explicitly skip empty text parts to avoid emitting empty text deltas.
            if content == "":
                continue

            if not started:
                yield StreamEvent.text_start(part_id)
                started = True

            yield StreamEvent.text_delta(part_id, content)

    if started:
        yield StreamEvent.text_end(part_id)
