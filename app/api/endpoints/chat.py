from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from app.api.core.log import get_logger
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
    last_msg = messages[-1]
    if isinstance(last_msg.get("content"), str):
        last_message = last_msg["content"]
    else:
        parts = last_msg.get("parts", [])
        last_message = "".join(p.get("text", "") for p in parts if p.get("type") == "text")

    if not last_message:
        return JSONResponse({"error": "no message content"}, status_code=400)

    session_id = data.get("id", "default_session")
    user_id = "default_user"
    runtime = (data.get("runtime") or "langchain").lower()

    if runtime == "langchain":
        stream = chat_service.stream_chat_response_langchain(
            user_id,
            session_id,
            last_message,
        )
    else:
        stream = chat_service.stream_chat_response_adk(
            user_id,
            session_id,
            last_message,
        )

    return StreamingResponse(
        stream,
        media_type="text/plain; charset=utf-8",
        headers={
            "x-vercel-ai-data-stream": "v1",
            "Cache-Control": "no-cache",
        },
    )
