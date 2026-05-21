from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.api.admin.tasks as tasks_api
from app.api.deps import get_db, verify_api_key
from app.database import Base
from app.models import Category, Keyword, CrawlTask, Video  # noqa: F401  ensure models registered


@pytest.fixture
def client(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    app = FastAPI()
    app.include_router(tasks_api.router)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_api_key] = lambda: "test-key"
    monkeypatch.setattr(
        tasks_api,
        "_enqueue_celery_task",
        lambda task_name, *args: f"task-{task_name}",
    )

    with TestClient(app) as c:
        c.session = TestingSessionLocal()
        yield c
        c.session.close()

    Base.metadata.drop_all(bind=engine)


def _create_keyword(session, keyword="python") -> Keyword:
    cat = session.query(Category).first()
    if cat is None:
        cat = Category(name="tech")
        session.add(cat)
        session.commit()
        session.refresh(cat)
    kw = Keyword(keyword=keyword, category_id=cat.id, status="active")
    session.add(kw)
    session.commit()
    session.refresh(kw)
    return kw


def _create_paused_keyword(session, keyword="paused") -> Keyword:
    kw = _create_keyword(session, keyword)
    kw.status = "paused"
    session.add(kw)
    session.commit()
    session.refresh(kw)
    return kw


def _create_video(session, keyword_id: int) -> Video:
    video = Video(
        external_id="v1",
        platform="bilibili",
        keyword_id=keyword_id,
        title="test video",
    )
    session.add(video)
    session.commit()
    session.refresh(video)
    return video


def _create_category_video(session, keyword_id: int, external_id: str, platform: str) -> Video:
    video = Video(
        external_id=external_id,
        platform=platform,
        keyword_id=keyword_id,
        title=f"{platform} video",
        publish_time=datetime(2026, 5, 21, 9, 0, 0),
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
        assert task.source == "manual"
        assert task.platform == "douyin"

    def test_creates_task_per_platform_when_platform_contains_multiple_values(self, client):
        kw = _create_keyword(client.session)

        response = client.post(
            "/api/admin/tasks/crawl",
            json={"keyword_id": kw.id, "platform": "bilibili,douyin"},
        )

        assert response.status_code == 202
        body = response.json()
        assert body["status"] == "pending"

        tasks = client.session.query(CrawlTask).order_by(CrawlTask.id).all()
        assert [task.platform for task in tasks] == ["bilibili", "douyin"]

    def test_returns_404_when_keyword_missing(self, client):
        response = client.post(
            "/api/admin/tasks/crawl", json={"keyword_id": 9999}
        )
        assert response.status_code == 404

    def test_rejects_inactive_keyword(self, client):
        kw = _create_paused_keyword(client.session)

        response = client.post(
            "/api/admin/tasks/crawl", json={"keyword_id": kw.id}
        )

        assert response.status_code == 400


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
        assert task.source == "manual"

    def test_with_keyword_id(self, client):
        kw = _create_keyword(client.session)
        # 新合约:keyword_id 模式按 publish_time 取最新 N 条 video,
        # 每个 video 一行 task。需要先插 video 才能验响应。
        _create_video(client.session, kw.id)
        response = client.post(
            "/api/admin/tasks/update", json={"keyword_id": kw.id}
        )
        assert response.status_code == 202
        body = response.json()
        assert body["keyword_id"] == kw.id
        assert body["video_count"] == 1
        assert len(body["task_ids"]) == 1
        assert body["status"] == "pending"

    def test_with_keyword_id_no_videos_returns_404(self, client):
        # keyword 存在但没有视频 → 404,前端能给提示
        kw = _create_keyword(client.session)
        response = client.post(
            "/api/admin/tasks/update", json={"keyword_id": kw.id}
        )
        assert response.status_code == 404

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

    def test_rejects_inactive_keyword(self, client):
        kw = _create_paused_keyword(client.session)

        response = client.post(
            "/api/admin/tasks/update", json={"keyword_id": kw.id}
        )

        assert response.status_code == 400

    def test_category_dispatch_filters_by_platform_when_provided(self, client):
        kw = _create_keyword(client.session)
        bili_video = _create_category_video(client.session, kw.id, "bili-1", "bilibili")
        _create_category_video(client.session, kw.id, "douyin-1", "douyin")

        task_ids, celery_task_ids, video_count = tasks_api.dispatch_update_category(
            client.session,
            kw.category_id,
            10,
            tasks_api._enqueue_celery_task,
            platform="bilibili",
        )

        assert video_count == 1
        assert celery_task_ids == ["task-update_videos"]
        task = client.session.query(CrawlTask).filter_by(id=task_ids[0]).first()
        assert task.video_ids == f"[{bili_video.id}]"


class TestListTasks:
    def test_returns_tasks_in_descending_order(self, client):
        kw = _create_keyword(client.session)
        t1 = CrawlTask(
            keyword_id=kw.id,
            platform="douyin",
            task_type="crawl",
            status="success",
            videos_crawled=5,
            source="manual",
            started_at=datetime(2024, 1, 1, 10, 0, 0),
        )
        t2 = CrawlTask(
            keyword_id=kw.id,
            platform="bilibili",
            task_type="update",
            status="success",
            videos_crawled=2,
            source="scheduled",
            source_id=3,
            started_at=datetime(2024, 1, 2, 10, 0, 0),
        )
        client.session.add_all([t1, t2])
        client.session.commit()

        response = client.get("/api/admin/tasks")
        assert response.status_code == 200
        body = response.json()
        # 新合约:返回 {total, data}
        assert body["total"] == 2
        assert len(body["data"]) == 2
        assert body["data"][0]["task_type"] == "update"
        assert body["data"][0]["platform"] == "bilibili"
        assert body["data"][0]["source"] == "scheduled"
        assert body["data"][0]["source_id"] == 3
        assert body["data"][1]["task_type"] == "crawl"
        assert body["data"][1]["platform"] == "douyin"
        assert body["data"][1]["source"] == "manual"

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
        body = response.json()
        assert body["total"] == 5
        assert len(body["data"]) == 2

        response = client.get("/api/admin/tasks?page=3&page_size=2")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 5
        assert len(body["data"]) == 1

    def test_legacy_null_source_is_returned_as_legacy(self, client):
        kw = _create_keyword(client.session)
        task = CrawlTask(
            keyword_id=kw.id,
            task_type="crawl",
            status="running",
            videos_crawled=0,
            source=None,
            started_at=datetime(2024, 1, 3, 10, 0, 0),
        )
        client.session.add(task)
        client.session.commit()
        client.session.execute(
            text("update crawl_tasks set source = null where id = :task_id"),
            {"task_id": task.id},
        )
        client.session.commit()

        response = client.get("/api/admin/tasks?page=1&page_size=20")

        assert response.status_code == 200
        body = response.json()
        assert body["data"][0]["source"] == "legacy"
