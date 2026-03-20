from fastapi import APIRouter
from app.api.endpoints import plan_router, chat_router

router = APIRouter()

router.include_router(plan_router, prefix="/plan", tags=["plan"])
router.include_router(chat_router, prefix="/chat", tags=["chat"])
