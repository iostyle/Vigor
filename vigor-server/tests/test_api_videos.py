from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.admin.videos import router
from app.api.deps import get_db, verify_api_key
from app.models.category import Category
from app.models.comment import CommentSummary
from app.models.keyword import Keyword
from app.models.task import CrawlTask
from app.models.video import Video


@pytest.fixture
def app(test_engine, test_db):
    from app.database import Base
    Base.metadata.create_all(bind=test_engine)

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: test_db
    app.dependency_overrides[verify_api_key] = lambda: "test-key"
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def seed_data(test_db):
    cat = Category(name="运动")
    test_db.add(cat)
    test_db.flush()

    keyword = Keyword(keyword="健身", category_id=cat.id, priority=1)
    test_db.add(keyword)
    test_db.flush()

    other_keyword = Keyword(keyword="瑜伽", category_id=cat.id, priority=2)
    test_db.add(other_keyword)
    test_db.flush()

    now = datetime.now()
    videos = [
        Video(
            external_id="dy_1",
            platform="douyin",
            keyword_id=keyword.id,
            title="recent fitness",
            author_name="alice",
            like_count=100,
            comment_count=10,
            share_count=5,
            heat_score=90.5,
            publish_time=now - timedelta(hours=2),
        ),
        Video(
            external_id="dy_2",
            platform="douyin",
            keyword_id=keyword.id,
            title="week-old fitness",
            author_name="bob",
            like_count=200,
            comment_count=20,
            share_count=10,
            heat_score=80.0,
            publish_time=now - timedelta(days=3),
        ),
        Video(
            external_id="dy_3",
            platform="douyin",
            keyword_id=keyword.id,
            title="old fitness",
            like_count=300,
            heat_score=50.0,
            publish_time=now - timedelta(days=40),
        ),
        Video(
            external_id="bili_4",
            platform="bilibili",
            keyword_id=other_keyword.id,
            title="yoga",
            heat_score=70.0,
            publish_time=now - timedelta(hours=5),
        ),
    ]
    test_db.add_all(videos)
    test_db.flush()

    summary = CommentSummary(
        video_id=videos[0].id,
        summary="users love it",
        top_keywords="good, amazing, love",
        sentiment="positive",
        comment_count=10,
    )
    test_db.add(summary)
    test_db.flush()

    return {
        "keyword_id": keyword.id,
        "other_keyword_id": other_keyword.id,
        "videos": videos,
    }


class TestListVideos:
    def test_returns_all_videos_default(self, client, seed_data):
        resp = client.get(
            "/api/admin/videos",
            params={"keyword_id": seed_data["keyword_id"]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert len(body["data"]) == 3

    def test_filter_by_keyword_id(self, client, seed_data):
        resp = client.get(
            "/api/admin/videos",
            params={"keyword_id": seed_data["keyword_id"]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert all(v["external_id"] in {"dy_1", "dy_2", "dy_3"} for v in body["data"])

    def test_filter_by_status(self, client, seed_data, test_db):
        video = seed_data["videos"][0]
        video.status = "hidden"
        test_db.commit()

        resp = client.get(
            "/api/admin/videos",
            params={"keyword_id": seed_data["keyword_id"], "video_status": "hidden"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["data"][0]["id"] == video.id
        assert body["data"][0]["status"] == "hidden"

    def test_accepts_douyin_platform_alias(self, client, seed_data):
        resp = client.get(
            "/api/admin/videos",
            params={"keyword_id": seed_data["keyword_id"], "platform": "dy"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert {v["platform"] for v in body["data"]} == {"douyin"}

    def test_filter_24h_window(self, client, seed_data):
        resp = client.get(
            "/api/admin/videos",
            params={"keyword_id": seed_data["keyword_id"], "time_window": "24h"},
        )
        assert resp.status_code == 200
        ids = {v["external_id"] for v in resp.json()["data"]}
        assert ids == {"dy_1"}

    def test_filter_7d_window(self, client, seed_data):
        resp = client.get(
            "/api/admin/videos",
            params={"keyword_id": seed_data["keyword_id"], "time_window": "7d"},
        )
        ids = {v["external_id"] for v in resp.json()["data"]}
        assert ids == {"dy_1", "dy_2"}

    def test_sort_by_heat_score_desc(self, client, seed_data):
        resp = client.get(
            "/api/admin/videos",
            params={"sort": "heat_score", "order": "desc"},
        )
        scores = [v["heat_score"] for v in resp.json()["data"]]
        assert scores == sorted(scores, reverse=True)

    def test_pagination(self, client, seed_data):
        resp = client.get(
            "/api/admin/videos",
            params={"keyword_id": seed_data["keyword_id"], "limit": 2, "offset": 0},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert len(body["data"]) == 2

        resp2 = client.get(
            "/api/admin/videos",
            params={"keyword_id": seed_data["keyword_id"], "limit": 2, "offset": 2},
        )
        assert len(resp2.json()["data"]) == 1

    def test_invalid_time_window(self, client, seed_data):
        resp = client.get("/api/admin/videos", params={"time_window": "bogus"})
        assert resp.status_code == 422


class TestGetVideo:
    def test_returns_video_with_summary(self, client, seed_data):
        video = seed_data["videos"][0]
        resp = client.get(f"/api/admin/videos/{video.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == video.id
        assert body["external_id"] == "dy_1"
        assert body["comment_summary"] is not None
        assert body["comment_summary"]["sentiment"] == "positive"
        assert body["comment_summary"]["top_keywords"] == ["good", "amazing", "love"]

    def test_returns_video_without_summary(self, client, seed_data):
        video = seed_data["videos"][1]
        resp = client.get(f"/api/admin/videos/{video.id}")
        assert resp.status_code == 200
        assert resp.json()["comment_summary"] is None

    def test_404_when_missing(self, client, seed_data):
        resp = client.get("/api/admin/videos/99999")
        assert resp.status_code == 404


class TestSummaryTaskStatus:
    def test_returns_running_summary_task(self, client, seed_data, test_db):
        video = seed_data["videos"][1]
        task = CrawlTask(
            keyword_id=video.keyword_id,
            video_ids=f"[{video.id}]",
            task_type="summary",
            status="running",
            videos_crawled=0,
            started_at=datetime.now(),
        )
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)

        resp = client.get(f"/api/admin/videos/{video.id}/summary-task")

        assert resp.status_code == 200
        body = resp.json()
        assert body["task_id"] == task.id
        assert body["status"] == "running"
        assert body["is_running"] is True

    def test_returns_not_running_without_summary_task(self, client, seed_data):
        video = seed_data["videos"][1]

        resp = client.get(f"/api/admin/videos/{video.id}/summary-task")

        assert resp.status_code == 200
        assert resp.json() == {"task_id": None, "status": None, "is_running": False}


class TestTriggerUpdate:
    def test_returns_202_and_dispatches_task(self, client, seed_data, monkeypatch):
        sent = {}

        class FakeResult:
            id = "task-abc"

        def fake_send_task(name, args, queue):
            sent["name"] = name
            sent["args"] = args
            sent["queue"] = queue
            return FakeResult()

        from app.celery_app import celery_app
        monkeypatch.setattr(celery_app, "send_task", fake_send_task)

        video = seed_data["videos"][0]
        resp = client.post(f"/api/admin/videos/{video.id}/update")
        assert resp.status_code == 202
        body = resp.json()
        assert body["task_id"] == "task-abc"
        assert body["video_id"] == video.id
        assert sent["name"] == "app.tasks.updater.update_single_video"
        assert sent["args"] == [video.id]
        assert sent["queue"] == "updater"

    def test_404_when_video_missing(self, client, seed_data):
        resp = client.post("/api/admin/videos/99999/update")
        assert resp.status_code == 404


class TestUpdateVideoStatus:
    def test_updates_video_status(self, client, seed_data, test_db):
        video = seed_data["videos"][0]

        resp = client.patch(
            f"/api/admin/videos/{video.id}/status",
            json={"status": "hidden"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == video.id
        assert body["status"] == "hidden"
        test_db.refresh(video)
        assert video.status == "hidden"

    def test_rejects_invalid_status(self, client, seed_data):
        video = seed_data["videos"][0]

        resp = client.patch(
            f"/api/admin/videos/{video.id}/status",
            json={"status": "deleted"},
        )

        assert resp.status_code == 422

    def test_404_when_video_missing(self, client, seed_data):
        resp = client.patch("/api/admin/videos/99999/status", json={"status": "hidden"})
        assert resp.status_code == 404
