from app.config import Settings


def test_settings_loads_from_env():
    settings = Settings()
    assert settings.DATABASE_URL is not None
    assert settings.REDIS_URL is not None
