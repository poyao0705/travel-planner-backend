import json
from google.adk.runners import Runner
from google.genai import types
from google.adk.agents.run_config import RunConfig, StreamingMode


class ChatService:
    def __init__(self, session_service, runner):
        self.session_service = session_service
        self.runner = runner
        self.app_name = "travel_planner"

    async def get_or_create_session(self, user_id: str, session_id: str):
        session = await self.session_service.get_session(
            app_name=self.app_name, user_id=user_id, session_id=session_id
        )
        if not session:
            await self.session_service.create_session(
                app_name=self.app_name, user_id=user_id, session_id=session_id
            )

    async def stream_chat_response_vercel(
        self, user_id: str, session_id: str, message_text: str
    ):
        await self.get_or_create_session(user_id, session_id)

        run_config = RunConfig(streaming_mode=StreamingMode.SSE)

        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(
                role="user", parts=[types.Part.from_text(text=message_text)]
            ),
            run_config=run_config
        ):
            # When StreamingMode.SSE is used, the ADK runner yields "partial" events
            # that contain the new token chunks directly. We don't need to diff!
            if event.partial and event.content and event.content.parts:
                has_text = any(p.text for p in event.content.parts)
                has_fc = any(p.function_call for p in event.content.parts)

                if has_text and not has_fc:
                    text_chunk = "".join(p.text or "" for p in event.content.parts)
                    if text_chunk:
                        yield f"0:{json.dumps(text_chunk)}\n"

        yield 'd:{"finishReason":"stop","usage":{"promptTokens":0,"completionTokens":0}}\n'
