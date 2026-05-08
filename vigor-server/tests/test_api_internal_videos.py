import importlib
import json
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base
from app.models import Comment, CommentSummary, Keyword, Video


@pytest.fixture()
def client(monkeypatch):
    module = importlib.import_module("app.api.internal.videos")

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
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


HEADERS = {"X-API-Key": "test-key"}


def _seed_videos(session_factory):
    session = session_factory()
    keyword = Keyword(keyword="美食", status="active")
    other = Keyword(keyword="科技", status="active")
    session.add_all([keyword, other])
    session.commit()
    session.refresh(keyword)
    session.refresh(other)

    now = datetime.utcnow()
    v1 = Video(
        external_id="v1",
        keyword_id=keyword.id,
        title="视频1",
        heat_score=9000.0,
        publish_time=now - timedelta(days=1),
    )
    v2 = Video(
        external_id="v2",
        keyword_id=keyword.id,
        title="视频2",
        heat_score=5000.0,
        publish_time=now - timedelta(days=2),
    )
    v3 = Video(
        external_id="v3",
        keyword_id=other.id,
        title="视频3",
        heat_score=8000.0,
        publish_time=now - timedelta(days=10),
    )
    session.add_all([v1, v2, v3])
    session.commit()
    session.refresh(v1)
    session.refresh(v2)
    session.refresh(v3)
    ids = (v1.id, v2.id, v3.id, keyword.id, other.id)
    session.close()
    return ids


def test_list_videos_requires_api_key(client):
    test_client, _ = client
    response = test_client.get("/api/videos")
    assert response.status_code == 403


def test_list_videos_returns_all_when_no_filters(client):
    test_client, factory = client
    _seed_videos(factory)
    response = test_client.get("/api/videos", headers=HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["data"]) == 3
    heat_scores = [v["heat_score"] for v in body["data"]]
    assert heat_scores == sorted(heat_scores, reverse=True)


def test_list_videos_filters_by_keyword(client):
    test_client, factory = client
    _, _, _, kw_id, _ = _seed_videos(factory)
    response = test_client.get(
        f"/api/videos?keyword_id={kw_id}", headers=HEADERS
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert all(v["external_id"] in ("v1", "v2") for v in body["data"])


def test_list_videos_filters_by_time_window(client):
    test_client, factory = client
    _seed_videos(factory)
    response = test_client.get(
        "/api/videos?time_window=3d", headers=HEADERS
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2


def test_list_videos_sort_by_publish_time(client):
    test_client, factory = client
    _seed_videos(factory)
    response = test_client.get(
        "/api/videos?sort=publish_time", headers=HEADERS
    )
    assert response.status_code == 200
    body = response.json()
    times = [v["publish_time"] for v in body["data"]]
    assert times == sorted(times, reverse=True)


def test_list_videos_pagination(client):
    test_client, factory = client
    _seed_videos(factory)
    response = test_client.get(
        "/api/videos?limit=1&offset=1", headers=HEADERS
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["data"]) == 1


def test_get_video_returns_detail(client):
    test_client, factory = client
    v1_id, *_ = _seed_videos(factory)
    response = test_client.get(f"/api/videos/{v1_id}", headers=HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == v1_id
    assert body["external_id"] == "v1"


def test_get_video_404(client):
    test_client, factory = client
    _seed_videos(factory)
    response = test_client.get("/api/videos/999999", headers=HEADERS)
    assert response.status_code == 404


def test_get_video_comments(client):
    test_client, factory = client
    v1_id, *_ = _seed_videos(factory)
    session = factory()
    session.add_all(
        [
            Comment(
                video_id=v1_id,
                external_comment_id="c1",
                content="评论1",
                like_count=100,
            ),
            Comment(
                video_id=v1_id,
                external_comment_id="c2",
                content="评论2",
                like_count=300,
            ),
        ]
    )
    session.commit()
    session.close()

    response = test_client.get(
        f"/api/videos/{v1_id}/comments", headers=HEADERS
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["like_count"] == 300
    assert body[1]["like_count"] == 100


def test_get_video_comments_404_when_video_missing(client):
    test_client, factory = client
    _seed_videos(factory)
    response = test_client.get(
        "/api/videos/999999/comments", headers=HEADERS
    )
    assert response.status_code == 404


def test_get_video_summary_with_comment_summary(client):
    test_client, factory = client
    v1_id, *_ = _seed_videos(factory)
    session = factory()
    session.add(
        CommentSummary(
            video_id=v1_id,
            summary="用户关注火候",
            top_keywords=json.dumps(["火候", "调料"]),
            sentiment="positive",
            generated_at=datetime(2026, 5, 7, 12, 0, 0),
            comment_count=42,
        )
    )
    session.commit()
    session.close()

    response = test_client.get(
        f"/api/videos/{v1_id}/summary", headers=HEADERS
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == v1_id
    assert body["comment_summary"] is not None
    assert body["comment_summary"]["summary"] == "用户关注火候"
    assert body["comment_summary"]["top_keywords"] == ["火候", "调料"]
    assert body["comment_summary"]["sentiment"] == "positive"
    assert body["comment_summary"]["comment_count"] == 42


def test_get_video_summary_without_comment_summary(client):
    test_client, factory = client
    v1_id, *_ = _seed_videos(factory)
    response = test_client.get(
        f"/api/videos/{v1_id}/summary", headers=HEADERS
    )
    assert response.status_code == 200
    body = response.json()
    assert body["comment_summary"] is None


def test_get_video_summary_404(client):
    test_client, factory = client
    _seed_videos(factory)
    response = test_client.get(
        "/api/videos/999999/summary", headers=HEADERS
    )
    assert response.status_code == 404
