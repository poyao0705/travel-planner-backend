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


def _extract_message_text(message: object) -> str:
    """Return joined text content from a LangChain AI message or chunk."""
    return "".join(_extract_text_chunks(message))

async def langchain_events_to_internal(events, *, out: dict | None = None):
    """Translate LangGraph astream events into the shared internal stream format."""
    text_part_id = f"text_{uuid.uuid4().hex}"
    text_started = False
    latest_values: Any = None
    streamed_text = ""

    async for part in events:
        part_type = part.get("type")

        if part_type == "messages":
            message, _ = part["data"]
            if isinstance(message, AIMessageChunk):
                text_chunks = _extract_text_chunks(message)

                if text_chunks:
                    chunk_text = "".join(text_chunks)
                    streamed_text += chunk_text
                    if not text_started:
                        yield StreamEvent.text_start(text_part_id)
                        text_started = True
                    yield StreamEvent.text_delta(text_part_id, chunk_text)

            elif isinstance(message, AIMessage):
                message_text = _extract_message_text(message)
                if not message_text:
                    continue

                if streamed_text and message_text == streamed_text:
                    streamed_text = ""
                    continue

                if not text_started:
                    yield StreamEvent.text_start(text_part_id)
                    text_started = True
                yield StreamEvent.text_delta(text_part_id, message_text)
                streamed_text = ""

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
