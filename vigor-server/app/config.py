from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    DATABASE_URL: str
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    DOUYIN_API_KEY: str
    DOUBAO_API_KEY: str
    SECRET_KEY: str
    API_KEY: str
    DOUBAO_MOCK_MODE: bool = True
    DOUYIN_MOCK_MODE: bool = True
    DOUYIN_API_BASE_URL: str = "https://api.douyin.example.com"
    DOUYIN_MAX_CONCURRENCY: int = 5
    # B 站默认 mock,真实链路需要登录态,先保守
    BILIBILI_MOCK_MODE: bool = True
    BILIBILI_MAX_CONCURRENCY: int = 3
    ENVIRONMENT: str = "development"


settings = Settings()
