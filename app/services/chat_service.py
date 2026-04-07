from app.services.agents.agno.utils.agno_stream import agno_events_to_internal
from app.services.agents.agno.workflows.travel_planner import travel_planner_workflow
from app.services.agents.stream import (
    StreamEvent,
    StreamContext,
    build_message_id,
    stream_events_to_vercel_sse,
)


class ChatService:
    def _agno_session_id(self, user_id: str, session_id: str) -> str:
        return f"{user_id}:{session_id}"

    def _build_agno_events(self, context: StreamContext):
        return travel_planner_workflow.arun(
            input=context.message_text,
            user_id=context.user_id,
            session_id=self._agno_session_id(context.user_id, context.session_id),
            markdown=True,
            stream=True,
            stream_events=True,
            stream_executor_events=False,
        )

    async def _stream_agno_events(self, context: StreamContext):
        yield StreamEvent.start(context.message_id)

        session_id = self._agno_session_id(context.user_id, context.session_id)
        events = self._build_agno_events(context)
        async for chunk in agno_events_to_internal(
            events,
            workflow=travel_planner_workflow,
            session_id=session_id,
        ):
            yield chunk

        yield StreamEvent.finish()

    async def stream_chat_response_agno(
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

        async for chunk in stream_events_to_vercel_sse(self._stream_agno_events(context)):
            yield chunk

