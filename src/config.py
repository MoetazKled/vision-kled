"""Application settings loaded from environment variables."""

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for Vision Kled Phase 0."""

    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    database_url: str = Field(
        default="sqlite:///visionkled.db",
        validation_alias=AliasChoices("DATABASE_URL", "VK_DATABASE_URL"),
    )
    demo_base_url: str = "http://127.0.0.1:8003"
    api_host: str = "127.0.0.1"
    api_port: int = 8003
    chainlit_port: int = 8001

    founder_name: str = "Moetez Khaled"
    brand_name: str = "Vision Kled"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
