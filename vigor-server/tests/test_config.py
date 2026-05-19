from app.config import Settings


def test_settings_loads_from_env():
    settings = Settings()
    assert settings.DATABASE_URL is not None
    assert settings.REDIS_URL is not None


def test_env_example_documents_all_settings_fields():
    settings_fields = set(Settings.model_fields)
    example_fields = set()
    with open(".env.example", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, _ = stripped.split("=", 1)
            example_fields.add(key)

    assert settings_fields - example_fields == set()
