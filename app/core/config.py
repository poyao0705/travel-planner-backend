from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    model_provider: str = "openrouter"
    chat_model: str = "openai/gpt-5.4"
    summary_model: str = "openai/gpt-5.4-mini"


settings = Settings()
