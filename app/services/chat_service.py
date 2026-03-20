import json
from google.adk.runners import Runner
from google.genai import types


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

        last_yielded_text = ""

        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(
                role="user", parts=[types.Part.from_text(text=message_text)]
            ),
        ):
            # Logic to extract delta text
            text_content = (
                "".join([p.text for p in event.content.parts if p.text])
                if event.content
                else ""
            )

            if text_content and text_content.startswith(last_yielded_text):
                delta = text_content[len(last_yielded_text) :]
                if delta:
                    yield f"0:{json.dumps(delta)}\n"
                    last_yielded_text = text_content
