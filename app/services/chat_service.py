import json
import uuid

from google.genai import types
from google.adk.agents.run_config import RunConfig, StreamingMode

from app.services.agents.langchain.agent import get_coordinator_agent
from app.services.agents.adk.adk_stream import adk_events_to_vercel_sse
from app.services.agents.langchain.langchain_stream import langchain_graph_to_vercel_sse


class ChatService:
    def __init__(self, session_service, runner):
        self.session_service = session_service
        self.runner = runner
        self.app_name = "travel_planner"

    def _session_kwargs(self, user_id: str, session_id: str) -> dict:
        return {
            "app_name": self.app_name,
            "user_id": user_id,
            "session_id": session_id,
        }

    async def ensure_session(self, user_id: str, session_id: str):
        kwargs = self._session_kwargs(user_id, session_id)

        session = await self.session_service.get_session(**kwargs)
        if session is None:
            session = await self.session_service.create_session(**kwargs)

        return session

    def _langchain_thread_id(self, user_id: str, session_id: str) -> str:
        return f"{user_id}:{session_id}"
    
    def build_ui_data(self, state: dict):
        # This function can be expanded to format the response in a way that's optimal for the frontend UI
        map_result = state.get("map_result")
        if not map_result:
            return {}

        if hasattr(map_result, "model_dump"):
            map_payload = map_result.model_dump()
        elif isinstance(map_result, dict):
            map_payload = map_result
        else:
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


    async def stream_chat_response_adk(
        self, user_id: str, session_id: str, message_text: str
    ):
        await self.ensure_session(user_id, session_id)

        run_config = RunConfig(streaming_mode=StreamingMode.SSE)

        message_id = f"msg_{uuid.uuid4().hex}"

        yield f"data: {json.dumps({'type': 'start', 'messageId': message_id})}\n\n"

        events = self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part.from_text(text=message_text)]),
            run_config=run_config,
        )
        async for chunk in adk_events_to_vercel_sse(events):
            yield chunk

        latest_session = await self.session_service.get_session(
            **self._session_kwargs(user_id, session_id)
        )
        state = (latest_session.state if latest_session else {}) or {}
        ui_data = self.build_ui_data(state)
        if ui_data:
            yield f"data: {json.dumps({'type': 'data-ui-data', 'data': ui_data})}\n\n" if ui_data else ""    
        yield f"data: {json.dumps({'type': 'finish'})}\n\n"
        yield "data: [DONE]\n\n"

    async def stream_chat_response_langchain(
        self, user_id: str, session_id: str, message_text: str
    ):
        message_id = f"msg_{uuid.uuid4().hex}"
        thread_id = self._langchain_thread_id(user_id, session_id)

        yield f"data: {json.dumps({'type': 'start', 'messageId': message_id})}\n\n"

        state_out: dict = {}
        async for chunk in langchain_graph_to_vercel_sse(
            get_coordinator_agent(), message_text, thread_id, out=state_out
        ):
            yield chunk

        ui_data = self.build_ui_data(state_out.get("state", {}))
        if ui_data:
            yield f"data: {json.dumps({'type': 'data-ui-data', 'data': ui_data})}\n\n"

        yield f"data: {json.dumps({'type': 'finish'})}\n\n"
        yield "data: [DONE]\n\n"

        yield f"data: {json.dumps({'type': 'finish'})}\n\n"
        yield "data: [DONE]\n\n"
