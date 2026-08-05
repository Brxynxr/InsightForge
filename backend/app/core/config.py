from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "PromptForge"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://promptforge:promptforge@localhost:5432/promptforge"
    DATABASE_ECHO: bool = False

    REDIS_URL: str | None = None

    OPENAI_API_KEY: str | None = None
    AZURE_OPENAI_API_KEY: str | None = None
    AZURE_OPENAI_ENDPOINT: str | None = None

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    MAX_BATCH_SIZE: int = 5000
    DEFAULT_BATCH_SIZE: int = 1000
    TOKENIZER_ENCODING: str = "o200k_base"

    LLM_PRICE_PER_1K_TOKENS: float = 0.00015
    LLM_PRICE_PER_1M_TOKENS: float = 2.50
    LLM_MODEL: str = "gpt-4o-mini"

    ANALYZE_BATCH_SIZE: int = 50
    ANALYZE_MAX_CONCURRENT: int = 20

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]


settings = Settings()
