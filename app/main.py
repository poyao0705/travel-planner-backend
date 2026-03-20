from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Force load the .env in the root into the environment
load_dotenv(override=True)

from app.api.core.log import setup_logging
from app.api.v1 import router as v1

app = FastAPI()
setup_logging(level="INFO")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    return {"Hello": "World"}


app.include_router(v1, prefix="/api/v1")
