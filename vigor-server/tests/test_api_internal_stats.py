import importlib
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base
from app.models import Category, Keyword, Video


@pytest.fixture()
def client(monkeypatch):
    module = importlib.import_module("app.api.internal.stats")

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(module.router, prefix="/api")

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[module.get_db] = override_get_db
    monkeypatch.setattr(settings, "API_KEY", "test-key")

    with TestClient(app) as test_client:
        yield test_client, testing_session_local


def test_list_keyword_stats_returns_video_counts_and_average_heat(client):
    test_client, session_factory = client
    session = session_factory()
    cat = Category(name="测试")
    session.add(cat)
    session.commit()
    session.refresh(cat)
    keyword_food = Keyword(keyword="美食", category_id=cat.id, status="active")
    keyword_tech = Keyword(keyword="科技", category_id=cat.id, status="active")
    session.add_all([keyword_food, keyword_tech])
    session.commit()
    session.refresh(keyword_food)
    session.refresh(keyword_tech)
    keyword_food_id = keyword_food.id
    keyword_tech_id = keyword_tech.id

    session.add_all(
        [
            Video(
                external_id="food-1",
                keyword_id=keyword_food_id,
                title="视频1",
                heat_score=5000.0,
                publish_time=datetime(2026, 5, 6, 10, 0, 0),
            ),
            Video(
                external_id="food-2",
                keyword_id=keyword_food_id,
                title="视频2",
                heat_score=3000.0,
                publish_time=datetime(2026, 5, 6, 12, 0, 0),
            ),
            Video(
                external_id="tech-1",
                keyword_id=keyword_tech_id,
                title="视频3",
                heat_score=9000.0,
                publish_time=datetime(2026, 5, 5, 9, 0, 0),
            ),
        ]
    )
    session.commit()
    session.close()

    response = test_client.get(
        "/api/stats/keywords",
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2

    stats_by_keyword = {item["keyword"]: item for item in body}
    assert stats_by_keyword["美食"] == {
        "keyword_id": keyword_food_id,
        "keyword": "美食",
        "video_count": 2,
        "avg_heat_score": 4000.0,
    }
    assert stats_by_keyword["科技"] == {
        "keyword_id": keyword_tech_id,
        "keyword": "科技",
        "video_count": 1,
        "avg_heat_score": 9000.0,
    }


def test_list_trends_returns_daily_aggregates_for_last_seven_days(client, monkeypatch):
    test_client, session_factory = client
    fixed_now = datetime(2026, 5, 7, 12, 0, 0)
    module = importlib.import_module("app.api.internal.stats")

    class FixedDateTime(datetime):
        @classmethod
        def utcnow(cls):
            return fixed_now

    monkeypatch.setattr(module, "datetime", FixedDateTime)

    session = session_factory()
    cat = Category(name="测试2")
    session.add(cat)
    session.commit()
    session.refresh(cat)
    keyword = Keyword(keyword="美食", category_id=cat.id, status="active")
    session.add(keyword)
    session.commit()
    session.refresh(keyword)

    session.add_all(
        [
            Video(
                external_id="recent-1",
                keyword_id=keyword.id,
                title="视频1",
                heat_score=4000.0,
                publish_time=fixed_now - timedelta(days=1, hours=1),
            ),
            Video(
                external_id="recent-2",
                keyword_id=keyword.id,
                title="视频2",
                heat_score=2000.0,
                publish_time=fixed_now - timedelta(days=1, hours=3),
            ),
            Video(
                external_id="recent-3",
                keyword_id=keyword.id,
                title="视频3",
                heat_score=3000.0,
                publish_time=fixed_now - timedelta(days=6),
            ),
            Video(
                external_id="old-1",
                keyword_id=keyword.id,
                title="视频4",
                heat_score=9999.0,
                publish_time=fixed_now - timedelta(days=8),
            ),
        ]
    )
    session.commit()
    session.close()

    response = test_client.get(
        "/api/stats/trends",
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200
    assert response.json() == [
        {"date": "2026-05-01", "video_count": 1, "avg_heat_score": 3000.0},
        {"date": "2026-05-06", "video_count": 2, "avg_heat_score": 3000.0},
    ]


def test_stats_api_requires_api_key(client):
    test_client, _ = client

    response = test_client.get("/api/stats/keywords")

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid or missing API key"
