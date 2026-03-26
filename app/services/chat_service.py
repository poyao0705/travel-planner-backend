from langchain.messages import HumanMessage

from app.services.agents.agent import DEFAULT_GRAPH_VARIANT, get_travel_agent
from app.services.agents.langchain_stream import langchain_events_to_internal
from app.services.agents.stream import (
    LangChainExecutor,
    StreamContext,
    StreamPipeline,
    build_message_id,
    normalize_mapping,
    stream_events_to_vercel_sse,
)


class ChatService:
    def __init__(self):
        self.langchain_stream = StreamPipeline(
            executor=LangChainExecutor(
                self._build_langchain_events,
                self._adapt_langchain_events,
            ),
            transformer=self._build_langchain_ui_data,
        )

    def _langchain_thread_id(self, user_id: str, session_id: str) -> str:
        return f"{user_id}:{session_id}"

    def build_ui_data(self, state: dict):
        state_payload = normalize_mapping(state)
        if not state_payload:
            return {}

        map_result = state_payload.get("map_result")
        if not map_result:
            return {}

        map_payload = normalize_mapping(map_result)
        if not map_payload:
            return {}

        center = map_payload.get("center")
        zoom = map_payload.get("zoom")
        if not center or zoom is None:
            return {}

        return {
            "map": {
                "center": center,
                "zoom": zoom,
                "displayName": map_payload.get("display_name"),
                "query": map_payload.get("query"),
            },
            # Include other state information as needed
        }

    def _build_langchain_events(self, context: StreamContext):
        graph_variant = context.run_config.get("graph_variant", DEFAULT_GRAPH_VARIANT)
        return get_travel_agent(graph_variant).astream(
            {"messages": [HumanMessage(content=context.message_text)]},
            context.run_config,
            stream_mode=["messages", "values"],
            version="v2",
        )

    async def _adapt_langchain_events(self, events, context: StreamContext):
        state_out = context.run_config.setdefault("state_out", {})
        async for chunk in langchain_events_to_internal(events, out=state_out):
            yield chunk

    async def _build_langchain_ui_data(self, context: StreamContext):
        state_out = context.run_config.get("state_out", {})
        state = state_out.get("state", {}) if isinstance(state_out, dict) else {}
        return self.build_ui_data(state)

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
                "state_out": {},
            },
        )

        async for chunk in stream_events_to_vercel_sse(
            self.langchain_stream.stream(context)
        ):
            yield chunk



