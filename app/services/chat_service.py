import uuid

from app.services.agents.langchain.agent import graph as langgraph_graph
from app.services.agents.langchain.utils.langgraph_stream import (
    langgraph_events_to_internal,
)
from app.services.agents.stream import (
    StreamEvent,
    StreamContext,
    build_message_id,
    stream_events_to_vercel_sse,
)


class ChatService:
    def _langgraph_thread_id(self, user_id: str, session_id: str) -> str:
        return f"{user_id}:{session_id}"

    async def _stream_langgraph_events(self, context: StreamContext):
        yield StreamEvent.start(context.message_id)

        part_id = f"text_{uuid.uuid4().hex}"
        config = {
            "configurable": {
                "thread_id": self._langgraph_thread_id(
                    context.user_id, context.session_id
                ),
            }
        }
        events = langgraph_graph.astream(
            {"messages": [{"role": "user", "content": context.message_text}]},
            config=config,
            stream_mode="messages",
        )

        async for chunk in langgraph_events_to_internal(events, part_id=part_id):
            yield chunk

        yield StreamEvent.finish()

    async def stream_chat_response_langgraph(
        self,
        user_id: str,
        session_id: str,
        message_text: str,
    ):
        context = StreamContext(
            user_id=user_id,
            session_id=session_id,
            message_text=message_text,
            message_id=build_message_id(),
        )

        async for chunk in stream_events_to_vercel_sse(
            self._stream_langgraph_events(context)
        ):
            yield chunk

