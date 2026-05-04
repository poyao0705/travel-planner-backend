from langchain.chat_models import init_chat_model

from app.core.config import settings


def build_model(model: str):
    return init_chat_model(
        model_provider=settings.model_provider,
        model=model,
        temperature=0,
        max_tokens=1024,
    )
