import uuid
from typing import Any

from langchain_core.messages import AIMessageChunk

from app.services.agents.langchain.stream import StreamEvent


def _extract_text_chunks(message: object) -> list[str]:
    """Return text chunks from a LangChain message or message chunk."""
    if not isinstance(message, (AIMessageChunk)):
        return []

    text_chunks: list[str] = []

    content_blocks = getattr(message, "content_blocks", None) or []
    for block in content_blocks:
        if block.get("type") == "text":
            text = block.get("text")
            if isinstance(text, str) and text:
                text_chunks.append(text)

    return text_chunks


async def langchain_events_to_internal(events):
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
        
        # This is where we pass to the UI of the AI agent state
        elif part_type == "values":
            latest_values = part["data"].model_dump() if hasattr(part["data"], "model_dump") else part["data"]

    if text_started:
        yield StreamEvent.text_end(text_part_id)

    # After all messages have been streamed, send the latest values one more time to ensure the UI has the final state
    if latest_values is not None:
        yield StreamEvent.ui(latest_values)
