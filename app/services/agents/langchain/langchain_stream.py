import json
import uuid

from langchain_core.messages import AIMessage, AIMessageChunk
from app.core.log import get_logger

logger = get_logger(__name__)

def _message_content(message: object) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(str(part.get("text", "")))
            elif hasattr(part, "text"):
                text_parts.append(str(getattr(part, "text", "")))
        return " ".join(p for p in text_parts if p)
    return str(content)


def _latest_assistant_text(messages: list[object]) -> str:
    for message in reversed(messages):
        if getattr(message, "type", "") in {"ai", "assistant"}:
            return _message_content(message)
    return ""


def _extract_stream_blocks(message: object) -> tuple[list[str], list[str]]:
    if not isinstance(message, (AIMessage, AIMessageChunk)):
        return [], []

    reasoning_chunks: list[str] = []
    text_chunks: list[str] = []
    for block in message.content_blocks:
        block_type = block.get("type")
        if block_type == "reasoning":
            reasoning = block.get("reasoning")
            if isinstance(reasoning, str) and reasoning:
                reasoning_chunks.append(reasoning)
        elif block_type == "text":
            text = block.get("text")
            if isinstance(text, str) and text:
                text_chunks.append(text)

    return reasoning_chunks, text_chunks


async def langchain_graph_to_vercel_sse(graph, message_text: str, thread_id: str, *, out: dict | None = None):
    """Translate a LangGraph graph's astream output into Vercel AI SDK SSE strings.

    Yields SSE chunks for reasoning and text content. Populates ``out["state"]``
    with the final graph values snapshot when ``out`` is provided.
    """
    text_part_id = f"text_{uuid.uuid4().hex}"
    reasoning_part_id = f"reasoning_{uuid.uuid4().hex}"
    text_started = False
    reasoning_started = False
    latest_values = None

    try:
        async for mode, payload in graph.astream(
            {"messages": [{"role": "user", "content": message_text}]},
            {"configurable": {"thread_id": thread_id}},
            stream_mode=["messages", "values"],
        ):
            if mode == "messages":
                message, _metadata = payload
                reasoning_chunks, text_chunks = _extract_stream_blocks(message)
                logger.info(f"Extracted {len(reasoning_chunks)} reasoning chunks and {len(text_chunks)} text chunks from message stream.")

                if reasoning_chunks:
                    if not reasoning_started:
                        yield f"data: {json.dumps({'type': 'reasoning-start', 'id': reasoning_part_id})}\n\n"
                        reasoning_started = True
                    yield f"data: {json.dumps({'type': 'reasoning-delta', 'id': reasoning_part_id, 'delta': ''.join(reasoning_chunks)})}\n\n"

                if text_chunks:
                    if not text_started:
                        yield f"data: {json.dumps({'type': 'text-start', 'id': text_part_id})}\n\n"
                        text_started = True
                    yield f"data: {json.dumps({'type': 'text-delta', 'id': text_part_id, 'delta': ''.join(text_chunks)})}\n\n"

            elif mode == "values":
                latest_values = payload

        result = latest_values or {}

        if not text_started:
            response_text = _latest_assistant_text(result.get("messages", []))
            if not response_text:
                response_text = "Destination intake completed."
            yield f"data: {json.dumps({'type': 'text-start', 'id': text_part_id})}\n\n"
            yield f"data: {json.dumps({'type': 'text-delta', 'id': text_part_id, 'delta': response_text})}\n\n"
            text_started = True

    except (RuntimeError, TypeError, ValueError) as exc:
        result = {}
        error_text = f"LangChain coordinator failed: {exc}"
        yield f"data: {json.dumps({'type': 'text-start', 'id': text_part_id})}\n\n"
        yield f"data: {json.dumps({'type': 'text-delta', 'id': text_part_id, 'delta': error_text})}\n\n"
        text_started = True

    if reasoning_started:
        yield f"data: {json.dumps({'type': 'reasoning-end', 'id': reasoning_part_id})}\n\n"
    if text_started:
        yield f"data: {json.dumps({'type': 'text-end', 'id': text_part_id})}\n\n"

    if out is not None:
        out["state"] = result
