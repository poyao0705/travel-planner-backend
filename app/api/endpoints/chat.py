from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from app.api.core.log import get_logger
from app.services.agent import root_agent

from google.adk.sessions import InMemorySessionService
from app.services.chat_service import ChatService
from app.dependencies import get_chat_service

router = APIRouter()
logger = get_logger(__name__)


@router.post("")
async def chat_endpoint(
    request: Request, chat_service: ChatService = Depends(get_chat_service)
):
    data = await request.json()
    messages = data.get("messages", [])

    if not messages:
        return JSONResponse({"error": "no messages"}, status_code=400)

    # Extracting identifiers
    last_message = messages[-1]["content"]
    session_id = data.get("id", "default_session")
    user_id = "default_user"

    return StreamingResponse(
        chat_service.stream_chat_response_vercel(user_id, session_id, last_message),
        media_type="text/event-stream",
    )
