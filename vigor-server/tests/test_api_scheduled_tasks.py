from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.admin.scheduled_tasks import router
from app.api.deps import get_db, verify_api_key
from app.database import Base
from app.models import Category, CrawlTask, Keyword, ScheduledTask, ScheduledTaskRun, Video  # noqa: F401


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

    with TestClient(app) as test_client:
        test_client.session = TestingSessionLocal()
        yield test_client
        test_client.session.close()

    Base.metadata.drop_all(bind=engine)


def _create_keyword(session) -> Keyword:
    cat = Category(name="影视")
    session.add(cat)
    session.commit()
    session.refresh(cat)
    kw = Keyword(keyword="电影", category_id=cat.id, status="active")
    session.add(kw)
    session.commit()
    session.refresh(kw)
    return kw


def _create_video(session, keyword_id: int) -> Video:
    video = Video(external_id="v1", keyword_id=keyword_id, title="测试视频")
    session.add(video)
    session.commit()
    session.refresh(video)
    return video


def test_create_interval_crawl_schedule(client):
    kw = _create_keyword(client.session)

    response = client.post(
        "/api/admin/scheduled-tasks",
        json={
            "name": "每小时爬取电影",
            "task_kind": "crawl",
            "target_mode": "keyword",
            "target_id": kw.id,
            "platform": "bilibili",
            "schedule_type": "interval",
            "interval_minutes": 60,
            "enabled": True,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["next_run_at"] is not None
    assert body["target_label"] == "电影"


def test_create_daily_update_schedule(client):
    kw = _create_keyword(client.session)
    video = _create_video(client.session, kw.id)

    response = client.post(
        "/api/admin/scheduled-tasks",
        json={
            "name": "每天更新视频",
            "task_kind": "update",
            "target_mode": "video",
            "target_id": video.id,
            "schedule_type": "daily",
            "daily_time": "08:30",
            "enabled": True,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["daily_time"] == "08:30"
    assert body["target_label"] == "测试视频"


def test_rejects_crawl_video_schedule(client):
    kw = _create_keyword(client.session)
    video = _create_video(client.session, kw.id)

    response = client.post(
        "/api/admin/scheduled-tasks",
        json={
            "name": "无效",
            "task_kind": "crawl",
            "target_mode": "video",
            "target_id": video.id,
            "schedule_type": "interval",
            "interval_minutes": 60,
        },
    )

    assert response.status_code == 400


def test_toggle_and_delete_schedule(client):
    kw = _create_keyword(client.session)
    task = ScheduledTask(
        name="待暂停",
        task_kind="crawl",
        target_mode="keyword",
        target_id=kw.id,
        platform="bilibili",
        schedule_type="interval",
        interval_minutes=60,
        enabled=True,
        next_run_at=datetime(2026, 5, 19, 8, 0, 0),
    )
    client.session.add(task)
    client.session.commit()
    client.session.refresh(task)

    response = client.patch(f"/api/admin/scheduled-tasks/{task.id}/enabled", json={"enabled": False})
    assert response.status_code == 200
    assert response.json()["enabled"] is False
    assert response.json()["next_run_at"] is None

    response = client.delete(f"/api/admin/scheduled-tasks/{task.id}")
    assert response.status_code == 204
    assert client.session.query(ScheduledTask).filter_by(id=task.id).first() is None


def test_monitor_returns_scheduler_health_and_stats(client):
    now = datetime.now()
    kw = _create_keyword(client.session)
    schedule = ScheduledTask(
        name="每小时爬取电影",
        task_kind="crawl",
        target_mode="keyword",
        target_id=kw.id,
        platform="bilibili",
        schedule_type="interval",
        interval_minutes=60,
        enabled=True,
        next_run_at=now + timedelta(minutes=30),
    )
    client.session.add(schedule)
    client.session.commit()
    client.session.refresh(schedule)

    run = ScheduledTaskRun(
        status="success",
        started_at=now,
        finished_at=now,
        due_count=1,
        dispatched_count=1,
        failed_count=0,
        triggered_task_ids="[100]",
    )
    task = CrawlTask(
        keyword_id=kw.id,
        task_type="crawl",
        source="scheduled",
        source_id=schedule.id,
        status="success",
        videos_crawled=3,
        started_at=now,
    )
    client.session.add_all([run, task])
    client.session.commit()

    response = client.get("/api/admin/scheduled-tasks/monitor")

    assert response.status_code == 200
    body = response.json()
    assert body["health"]["status"] in {"healthy", "delayed"}
    assert body["scheduler"]["last_dispatched_count"] == 1
    assert body["tasks"]["enabled_count"] == 1
    assert body["tasks"]["last_24h_total"] == 1
    assert body["recent_tasks"][0]["source"] == "scheduled"
    assert body["recent_runs"][0]["triggered_task_ids"] == [100]
