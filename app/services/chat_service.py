from langchain.messages import HumanMessage

from app.services.agents.agent import DEFAULT_GRAPH_VARIANT, get_travel_agent
from app.services.agents.langchain_stream import langchain_events_to_internal
from app.services.agents.stream import (
    StreamEvent,
    StreamContext,
    build_message_id,
    stream_events_to_vercel_sse,
)


class ChatService:
    def _langchain_thread_id(self, user_id: str, session_id: str) -> str:
        return f"{user_id}:{session_id}"

    def _build_langchain_events(self, context: StreamContext):
        graph_variant = context.run_config.get("graph_variant", DEFAULT_GRAPH_VARIANT)
        return get_travel_agent(graph_variant).astream(
            {"messages": [HumanMessage(content=context.message_text)]},
            context.run_config,
            stream_mode=["messages", "values"],
            version="v2",
        )

    async def _stream_langchain_events(self, context: StreamContext):
        yield StreamEvent.start(context.message_id)

        events = self._build_langchain_events(context)
        async for chunk in langchain_events_to_internal(events):
            yield chunk

        yield StreamEvent.finish()

    async def stream_chat_response_langchain(
        self,
        user_id: str,
        session_id: str,
        message_text: str,
        graph_variant: str = DEFAULT_GRAPH_VARIANT,
    ):
        context = StreamContext(
            user_id=user_id,
            session_id=session_id,
            message_text=message_text,
            message_id=build_message_id(),
            run_config={
                "graph_variant": graph_variant,
                "configurable": {"thread_id": self._langchain_thread_id(user_id, session_id)},
            },
        )

        async for chunk in stream_events_to_vercel_sse(
            self._stream_langchain_events(context)
        ):
            yield chunk

