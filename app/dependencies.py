from app.services.chat_service import ChatService


def get_chat_service() -> ChatService:
    """Dependency injector for ChatService"""
    return ChatService()
