from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

    DATABASE_URL: str
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    DOUYIN_API_KEY: str
    DOUBAO_API_KEY: str
    SECRET_KEY: str
    API_KEY: str
    ENVIRONMENT: str = "development"


settings = Settings()
