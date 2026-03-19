from fastapi import FastAPI
from app.api.v1 import router as v1
from app.api.core.log import setup_logging

app = FastAPI()
setup_logging(level="INFO")

@app.get("/")
async def read_root():
    return {"Hello": "World"}

app.include_router(v1, prefix="/api/v1")
