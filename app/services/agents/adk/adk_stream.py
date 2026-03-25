import json
import uuid


async def adk_events_to_vercel_sse(events):
    """Translates an async iterable of ADK SSE events into Vercel AI SDK SSE strings."""
    text_part_id = f"text_{uuid.uuid4().hex}"
    reasoning_part_id = f"reasoning_{uuid.uuid4().hex}"
    text_started = False
    reasoning_started = False

    async for event in events:
        if event.partial and event.content and event.content.parts:
            text_parts = []
            thought_parts = []
            has_fc = False

            for p in event.content.parts:
                if p.function_call:
                    has_fc = True
                if p.text and not p.thought:
                    text_parts.append(p.text)
                if p.thought:
                    thought_parts.append(p.text)

            if text_parts and not has_fc:
                if not text_started:
                    yield f"data: {json.dumps({'type': 'text-start', 'id': text_part_id})}\n\n"
                    text_started = True
                yield f"data: {json.dumps({'type': 'text-delta', 'id': text_part_id, 'delta': ''.join(text_parts)})}\n\n"

            if thought_parts:
                if not reasoning_started:
                    yield f"data: {json.dumps({'type': 'reasoning-start', 'id': reasoning_part_id})}\n\n"
                    reasoning_started = True
                yield f"data: {json.dumps({'type': 'reasoning-delta', 'id': reasoning_part_id, 'delta': ''.join(thought_parts)})}\n\n"

    if text_started:
        yield f"data: {json.dumps({'type': 'text-end', 'id': text_part_id})}\n\n"
    if reasoning_started:
        yield f"data: {json.dumps({'type': 'reasoning-end', 'id': reasoning_part_id})}\n\n"