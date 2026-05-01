from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.core.log import get_logger
from app.dependencies import get_chat_service
from app.services.chat_service import ChatService

router = APIRouter()
logger = get_logger(__name__)


def _extract_last_message_content(message: dict) -> str:
    if isinstance(message.get("content"), str):
        return message["content"]

    parts = message.get("parts", [])
    return "".join(part.get("text", "") for part in parts if part.get("type") == "text")


@router.post("")
async def chat_endpoint(
    request: Request, chat_service: ChatService = Depends(get_chat_service)
):
    data = await request.json()
    messages = data.get("messages", [])

    if not messages:
        return JSONResponse({"error": "no messages"}, status_code=400)

    last_message = _extract_last_message_content(messages[-1])

    if not last_message:
        return JSONResponse({"error": "no message content"}, status_code=400)

    session_id = data.get("id", "default_session")
    logger.info("session_id: %s", session_id)
    logger.info("last_message: %s", last_message)
    user_id = "default_user"

    logger.info("messages: %s", messages)

    stream = chat_service.stream_chat_response_langgraph(
        user_id, session_id, last_message
    )

    return StreamingResponse(
        stream,
        media_type="text/plain; charset=utf-8",
        headers={
            "x-vercel-ai-data-stream": "v1",
            "Cache-Control": "no-cache",
        },
    )
