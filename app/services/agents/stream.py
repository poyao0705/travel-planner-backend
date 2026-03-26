import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, AsyncIterable


DONE_SSE_EVENT = "data: [DONE]\n\n"


@dataclass(slots=True, frozen=True)
class StreamContext:
    user_id: str
    session_id: str
    message_text: str
    message_id: str
    run_config: Any | None = None


class StreamEvent:
    @staticmethod
    def start(message_id):
        return {"type": "start", "messageId": message_id}

    @staticmethod
    def token(text, part_id=None):
        payload = {"type": "text-delta", "delta": text}
        if part_id is not None:
            payload["id"] = part_id
        return payload

    @staticmethod
    def text_start(part_id):
        return {"type": "text-start", "id": part_id}

    @staticmethod
    def text_delta(part_id, text):
        return {"type": "text-delta", "id": part_id, "delta": text}

    @staticmethod
    def text_end(part_id):
        return {"type": "text-end", "id": part_id}

    @staticmethod
    def reasoning_start(part_id):
        return {"type": "reasoning-start", "id": part_id}

    @staticmethod
    def reasoning_delta(part_id, text):
        return {"type": "reasoning-delta", "id": part_id, "delta": text}

    @staticmethod
    def reasoning_end(part_id):
        return {"type": "reasoning-end", "id": part_id}

    @staticmethod
    def ui(data):
        return {"type": "data-ui-data", "data": data}

    @staticmethod
    def finish():
        return {"type": "finish"}

class StreamPipeline:
    def __init__(self, executor, transformer=None):
        self.executor = executor
        self.transformer = transformer

    async def stream(self, context):
        yield StreamEvent.start(context.message_id)

        async for event in self.executor.run(context):
            yield event

        if self.transformer:
            extra = await self.transformer(context)
            if extra:
                yield StreamEvent.ui(extra)

        yield StreamEvent.finish()


def build_message_id() -> str:
    return f"msg_{uuid.uuid4().hex}"


def encode_sse(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def normalize_mapping(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        if isinstance(dumped, Mapping):
            return dict(dumped)
        return {}

    if isinstance(value, Mapping):
        return dict(value)

    return {}


async def stream_events_to_vercel_sse(events: AsyncIterable[dict[str, Any]]):
    saw_finish = False

    async for event in events:
        yield encode_sse(event)
        if event.get("type") == "finish":
            saw_finish = True
            yield DONE_SSE_EVENT

    if not saw_finish:
        yield DONE_SSE_EVENT
class LangChainExecutor:
    def __init__(self, event_source, event_adapter):
        self.event_source = event_source
        self.event_adapter = event_adapter

    async def run(self, context):
        events = self.event_source(context)
        async for chunk in self.event_adapter(events, context):
            yield chunk