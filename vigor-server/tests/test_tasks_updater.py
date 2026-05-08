import importlib
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Keyword, Video


class FakeDouyinClient:
    def __init__(self, details):
        self.details = details
        self.requested_ids = []

    async def get_video_detail(self, video_id):
        self.requested_ids.append(video_id)
        return self.details[video_id]


@pytest.fixture()
def updater_module():
    return importlib.import_module("app.tasks.updater")


@pytest.fixture()
def session_factory():
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
    return testing_session_local


@pytest.fixture()
def fixed_now():
    return datetime(2026, 5, 7, 12, 0, 0)


def test_update_videos_task_updates_due_videos_by_heat_tier(
    updater_module,
    session_factory,
    fixed_now,
    monkeypatch,
):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    session = session_factory()
    keyword = Keyword(keyword="美食", status="active")
    session.add(keyword)
    session.commit()
    session.refresh(keyword)

    hot_due = Video(
        external_id="hot-due",
        keyword_id=keyword.id,
        title="hot",
        like_count=100,
        comment_count=10,
        share_count=5,
        heat_score=15000.0,
        publish_time=fixed_now - timedelta(days=1),
        last_updated_at=fixed_now - timedelta(hours=2),
    )
    hot_recent = Video(
        external_id="hot-recent",
        keyword_id=keyword.id,
        title="hot recent",
        like_count=100,
        comment_count=10,
        share_count=5,
        heat_score=15000.0,
        publish_time=fixed_now - timedelta(days=1),
        last_updated_at=fixed_now - timedelta(minutes=30),
    )
    mid_due = Video(
        external_id="mid-due",
        keyword_id=keyword.id,
        title="mid",
        like_count=80,
        comment_count=8,
        share_count=4,
        heat_score=5000.0,
        publish_time=fixed_now - timedelta(days=2),
        last_updated_at=fixed_now - timedelta(hours=7),
    )
    low_due = Video(
        external_id="low-due",
        keyword_id=keyword.id,
        title="low",
        like_count=10,
        comment_count=1,
        share_count=0,
        heat_score=500.0,
        publish_time=fixed_now - timedelta(days=3),
        last_updated_at=fixed_now - timedelta(hours=25),
    )
    session.add_all([hot_due, hot_recent, mid_due, low_due])
    session.commit()
    session.close()

    details = {
        "hot-due": {
            "external_id": "hot-due",
            "like_count": 300,
            "comment_count": 12,
            "share_count": 10,
            "publish_time": fixed_now.isoformat(),
        },
        "mid-due": {
            "external_id": "mid-due",
            "like_count": 120,
            "comment_count": 9,
            "share_count": 6,
            "publish_time": fixed_now.isoformat(),
        },
        "low-due": {
            "external_id": "low-due",
            "like_count": 20,
            "comment_count": 1,
            "share_count": 1,
            "publish_time": fixed_now.isoformat(),
        },
    }
    client = FakeDouyinClient(details)

    monkeypatch.setattr(updater_module, "SessionLocal", session_factory)
    monkeypatch.setattr(updater_module, "datetime", FixedDateTime)
    monkeypatch.setattr(updater_module, "_get_douyin_client", lambda: client)
    monkeypatch.setattr(
        updater_module,
        "calculate_heat_score",
        lambda like_count, comment_count, share_count, publish_time: (
            like_count + comment_count * 2 + share_count * 5
        ),
    )

    result = updater_module.update_videos_task.run()

    assert result == {
        "status": "success",
        "updated_count": 3,
        "comment_crawl_count": 0,
    }
    assert client.requested_ids == ["hot-due", "mid-due", "low-due"]

    verify_session = session_factory()
    hot_due_db = (
        verify_session.query(Video).filter(Video.external_id == "hot-due").first()
    )
    hot_recent_db = (
        verify_session.query(Video).filter(Video.external_id == "hot-recent").first()
    )
    mid_due_db = (
        verify_session.query(Video).filter(Video.external_id == "mid-due").first()
    )
    low_due_db = (
        verify_session.query(Video).filter(Video.external_id == "low-due").first()
    )

    assert hot_due_db.like_count == 300
    assert hot_due_db.comment_count == 12
    assert hot_due_db.share_count == 10
    assert hot_due_db.heat_score == 374
    assert hot_due_db.last_updated_at == fixed_now

    assert mid_due_db.like_count == 120
    assert mid_due_db.comment_count == 9
    assert mid_due_db.share_count == 6
    assert mid_due_db.heat_score == 168
    assert mid_due_db.last_updated_at == fixed_now

    assert low_due_db.like_count == 20
    assert low_due_db.comment_count == 1
    assert low_due_db.share_count == 1
    assert low_due_db.heat_score == 27
    assert low_due_db.last_updated_at == fixed_now

    assert hot_recent_db.like_count == 100
    assert hot_recent_db.comment_count == 10
    assert hot_recent_db.share_count == 5
    assert hot_recent_db.last_updated_at == fixed_now - timedelta(minutes=30)
    verify_session.close()


def test_update_videos_task_triggers_comment_recrawl_when_comment_growth_exceeds_twenty_percent(
    updater_module,
    session_factory,
    fixed_now,
    monkeypatch,
):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    session = session_factory()
    keyword = Keyword(keyword="科技", status="active")
    session.add(keyword)
    session.commit()
    session.refresh(keyword)

    video = Video(
        external_id="growth-video",
        keyword_id=keyword.id,
        title="growth",
        like_count=50,
        comment_count=10,
        share_count=2,
        heat_score=12000.0,
        publish_time=fixed_now - timedelta(hours=2),
        last_updated_at=fixed_now - timedelta(hours=2),
    )
    session.add(video)
    session.commit()
    session.refresh(video)
    video_id = video.id
    session.close()

    client = FakeDouyinClient(
        {
            "growth-video": {
                "external_id": "growth-video",
                "like_count": 60,
                "comment_count": 13,
                "share_count": 3,
                "publish_time": fixed_now.isoformat(),
            }
        }
    )
    sent = {}

    def fake_send_task(name, args, queue):
        sent["name"] = name
        sent["args"] = args
        sent["queue"] = queue

    monkeypatch.setattr(updater_module, "SessionLocal", session_factory)
    monkeypatch.setattr(updater_module, "datetime", FixedDateTime)
    monkeypatch.setattr(updater_module, "_get_douyin_client", lambda: client)
    monkeypatch.setattr(updater_module, "calculate_heat_score", lambda *args: 999.0)
    monkeypatch.setattr(updater_module.celery_app, "send_task", fake_send_task)

    result = updater_module.update_videos_task.run()

    assert result == {
        "status": "success",
        "updated_count": 1,
        "comment_crawl_count": 1,
    }
    assert sent == {
        "name": "app.tasks.crawler.crawl_video_comments",
        "args": [video_id],
        "queue": "crawler",
    }


def test_update_videos_task_queue_configuration(updater_module):
    assert updater_module.update_videos_task.name == "app.tasks.updater.update_videos"
    assert updater_module.update_videos_task.queue == "updater"
