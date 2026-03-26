import os

from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from app.core.log import get_logger
from app.services.agents.langchain.agent import (
    DEFAULT_GRAPH_VARIANT,
    SUPPORTED_GRAPH_VARIANTS,
)
from app.services.chat_service import ChatService
from app.dependencies import get_chat_service

router = APIRouter()
logger = get_logger(__name__)

GRAPH_SELECTOR_HEADER = "x-internal-graph"
GRAPH_SELECTOR_SECRET_HEADER = "x-internal-graph-secret"
DEVELOPMENT_ENVIRONMENTS = {"dev", "development", "local"}


def _is_development_mode() -> bool:
    environment = (
        os.getenv("APP_ENV")
        or os.getenv("ENVIRONMENT")
        or os.getenv("FASTAPI_ENV")
        or "production"
    )
    return environment.lower() in DEVELOPMENT_ENVIRONMENTS


def _is_trusted_graph_request(request: Request) -> bool:
    expected_secret = os.getenv("INTERNAL_GRAPH_SECRET", "").strip()
    if not expected_secret:
        return False

    provided_secret = request.headers.get(GRAPH_SELECTOR_SECRET_HEADER, "").strip()
    return provided_secret == expected_secret


def _resolve_graph_variant(request: Request, data: dict) -> str:
    requested_variant = (
        request.headers.get(GRAPH_SELECTOR_HEADER)
        or data.get("graph")
        or DEFAULT_GRAPH_VARIANT
    )
    return str(requested_variant).strip().lower() or DEFAULT_GRAPH_VARIANT


@router.post("")
async def chat_endpoint(
    request: Request, chat_service: ChatService = Depends(get_chat_service)
):
    data = await request.json()
    graph_variant = _resolve_graph_variant(request, data)

    if graph_variant not in SUPPORTED_GRAPH_VARIANTS:
        return JSONResponse({"error": f"unsupported graph variant: {graph_variant}"}, status_code=400)

    if graph_variant != DEFAULT_GRAPH_VARIANT and not (
        _is_development_mode() or _is_trusted_graph_request(request)
    ):
        return JSONResponse({"error": "experimental graph selection is not allowed"}, status_code=403)

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
    stream = chat_service.stream_chat_response_langchain(
        user_id,
        session_id,
        last_message,
        graph_variant=graph_variant,
    )

    return StreamingResponse(
        stream,
        media_type="text/plain; charset=utf-8",
        headers={
            "x-vercel-ai-data-stream": "v1",
            "Cache-Control": "no-cache",
        },
    )
