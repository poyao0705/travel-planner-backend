import json
import uuid
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

        message_id = f"msg_{uuid.uuid4().hex}"
        text_part_id = f"text_{uuid.uuid4().hex}"
        reasoning_part_id = f"reasoning_{uuid.uuid4().hex}"

        yield f"data: {json.dumps({'type': 'start', 'messageId': message_id})}\n\n"

        text_started = False
        reasoning_started = False

        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(
                role="user", parts=[types.Part.from_text(text=message_text)]
            ),
            run_config=run_config,
        ):
            # When StreamingMode.SSE is used, the ADK runner yields "partial" events
            # that contain the new token chunks directly. We don't need to diff!
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
                    text_chunk = "".join(text_parts)
                    if not text_started:
                        yield f"data: {json.dumps({'type': 'text-start', 'id': text_part_id})}\n\n"
                        text_started = True
                    yield f"data: {json.dumps({'type': 'text-delta', 'id': text_part_id, 'delta': text_chunk})}\n\n"

                if thought_parts:
                    thought_chunk = "".join(thought_parts)
                    if not reasoning_started:
                        yield f"data: {json.dumps({'type': 'reasoning-start', 'id': reasoning_part_id})}\n\n"
                        reasoning_started = True
                    yield f"data: {json.dumps({'type': 'reasoning-delta', 'id': reasoning_part_id, 'delta': thought_chunk})}\n\n"

        if text_started:
            yield f"data: {json.dumps({'type': 'text-end', 'id': text_part_id})}\n\n"
        if reasoning_started:
            yield f"data: {json.dumps({'type': 'reasoning-end', 'id': reasoning_part_id})}\n\n"
        yield f"data: {json.dumps({'type': 'finish'})}\n\n"
        yield "data: [DONE]\n\n"
