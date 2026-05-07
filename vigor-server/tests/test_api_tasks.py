from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.admin.tasks import router
from app.api.deps import get_db, verify_api_key
from app.database import Base
from app.models import Keyword, CrawlTask, Video  # noqa: F401  ensure models registered


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    app = FastAPI()
    app.include_router(router)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_api_key] = lambda: "test-key"

    with TestClient(app) as c:
        c.session = TestingSessionLocal()
        yield c
        c.session.close()

    Base.metadata.drop_all(bind=engine)


def _create_keyword(session, keyword="python") -> Keyword:
    kw = Keyword(keyword=keyword, category="tech", status="active")
    session.add(kw)
    session.commit()
    session.refresh(kw)
    return kw


def _create_video(session, keyword_id: int) -> Video:
    video = Video(
        douyin_id="v1",
        keyword_id=keyword_id,
        title="test video",
    )
    session.add(video)
    session.commit()
    session.refresh(video)
    return video


class TestTriggerCrawl:
    def test_creates_task_and_returns_202(self, client):
        kw = _create_keyword(client.session)

        response = client.post(
            "/api/admin/tasks/crawl", json={"keyword_id": kw.id}
        )

        assert response.status_code == 202
        body = response.json()
        assert body["task_id"] > 0
        assert body["celery_task_id"]
        assert body["status"] == "pending"

        task = client.session.query(CrawlTask).filter_by(id=body["task_id"]).first()
        assert task is not None
        assert task.task_type == "crawl"
        assert task.keyword_id == kw.id

    def test_returns_404_when_keyword_missing(self, client):
        response = client.post(
            "/api/admin/tasks/crawl", json={"keyword_id": 9999}
        )
        assert response.status_code == 404


class TestTriggerUpdate:
    def test_with_video_id(self, client):
        kw = _create_keyword(client.session)
        video = _create_video(client.session, kw.id)

        response = client.post(
            "/api/admin/tasks/update", json={"video_id": video.id}
        )

        assert response.status_code == 202
        body = response.json()
        task = client.session.query(CrawlTask).filter_by(id=body["task_id"]).first()
        assert task.task_type == "update"

    def test_with_keyword_id(self, client):
        kw = _create_keyword(client.session)
        response = client.post(
            "/api/admin/tasks/update", json={"keyword_id": kw.id}
        )
        assert response.status_code == 202

    def test_requires_at_least_one_id(self, client):
        response = client.post("/api/admin/tasks/update", json={})
        assert response.status_code == 400

    def test_returns_404_when_video_missing(self, client):
        response = client.post(
            "/api/admin/tasks/update", json={"video_id": 9999}
        )
        assert response.status_code == 404

    def test_returns_404_when_keyword_missing(self, client):
        response = client.post(
            "/api/admin/tasks/update", json={"keyword_id": 9999}
        )
        assert response.status_code == 404


class TestListTasks:
    def test_returns_tasks_in_descending_order(self, client):
        kw = _create_keyword(client.session)
        t1 = CrawlTask(
            keyword_id=kw.id,
            task_type="crawl",
            status="success",
            videos_crawled=5,
            started_at=datetime(2024, 1, 1, 10, 0, 0),
        )
        t2 = CrawlTask(
            keyword_id=kw.id,
            task_type="update",
            status="success",
            videos_crawled=2,
            started_at=datetime(2024, 1, 2, 10, 0, 0),
        )
        client.session.add_all([t1, t2])
        client.session.commit()

        response = client.get("/api/admin/tasks")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 2
        assert body[0]["task_type"] == "update"
        assert body[1]["task_type"] == "crawl"

    def test_pagination(self, client):
        kw = _create_keyword(client.session)
        for i in range(5):
            client.session.add(
                CrawlTask(
                    keyword_id=kw.id,
                    task_type="crawl",
                    status="success",
                    videos_crawled=0,
                    started_at=datetime(2024, 1, 1, 10, i, 0),
                )
            )
        client.session.commit()

        response = client.get("/api/admin/tasks?page=1&page_size=2")
        assert response.status_code == 200
        assert len(response.json()) == 2

        response = client.get("/api/admin/tasks?page=3&page_size=2")
        assert response.status_code == 200
        assert len(response.json()) == 1
