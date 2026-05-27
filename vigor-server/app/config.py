from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    DATABASE_URL: str
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:5173"
    DOUYIN_API_KEY: str
    DOUBAO_API_KEY: str
    DOUBAO_ENDPOINT_ID: str
    SECRET_KEY: str
    API_KEY: str
    DOUBAO_MOCK_MODE: bool = True
    AUTO_GENERATE_SUMMARY_AFTER_CRAWL: bool = False
    DOUYIN_MOCK_MODE: bool = True
    DOUYIN_API_BASE_URL: str = "https://api.douyin.example.com"
    DOUYIN_MAX_CONCURRENCY: int = 5
    DOUYIN_LOGIN_TYPE: str = "qrcode"
    DOUYIN_COOKIES: str = ""
    DOUYIN_ENABLE_CDP_MODE: bool = False
    DOUYIN_HEADLESS: bool = True
    # B 站默认 mock,真实链路需要登录态,先保守
    BILIBILI_MOCK_MODE: bool = True
    BILIBILI_MAX_CONCURRENCY: int = 3
    ENVIRONMENT: str = "development"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
