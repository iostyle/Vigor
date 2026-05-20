from app.api.deps import get_db, verify_api_key, verify_api_key_value
from app.config import settings


class FakeSession:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class TestGetDb:
    def test_yields_session_and_closes_it(self, monkeypatch):
        session = FakeSession()
        monkeypatch.setattr("app.api.deps.SessionLocal", lambda: session)

        generator = get_db()
        yielded = next(generator)
        assert yielded is session

        try:
            next(generator)
        except StopIteration:
            pass

        assert session.closed is True


class TestVerifyApiKey:
    def test_accepts_valid_key(self, monkeypatch):
        monkeypatch.setattr(settings, "API_KEY", "secret")
        assert verify_api_key("secret") == "secret"

    def test_rejects_invalid_key(self, monkeypatch):
        monkeypatch.setattr(settings, "API_KEY", "secret")

        try:
            verify_api_key("wrong")
        except Exception as exc:
            assert getattr(exc, "status_code", None) == 403
            assert getattr(exc, "detail", None) == "Invalid or missing API key"
        else:
            raise AssertionError("Expected HTTPException")

    def test_accepts_valid_query_key_value(self, monkeypatch):
        monkeypatch.setattr(settings, "API_KEY", "secret")
        assert verify_api_key_value("secret") == "secret"
