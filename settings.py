from functools import lru_cache
from pydantic_settings import BaseSettings , SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    RABBITMQ_URL: str
    API_SERVICE_URL: str
    MAX_RETRIES: int = 3
    WORKER_SERVICE_PREFETCH_COUNT: int = 5
    NOTIFICATION_SERVICE_PREFETCH_COUNT: int = 7
    SHORTNER_SERVICE: str
    REDIS_URL:str
    GMAIL_ADDRESS : str
    GMAIL_APP_PASSWORD : str
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings=get_settings()