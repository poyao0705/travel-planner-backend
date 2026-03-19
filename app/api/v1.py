from fastapi import APIRouter
from app.api.endpoints import plan_router

router = APIRouter()

router.include_router(plan_router, prefix="/plan", tags=["plan"])
