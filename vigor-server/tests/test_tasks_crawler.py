from datetime import datetime, timedelta, timezone

import pytest

from app.models.comment import Comment
from app.models.keyword import Keyword
from app.models.task import CrawlTask
from app.models.video import Video
from app.tasks import crawler


class FakeQuery:
    def __init__(self, data, session=None, model=None):
        self._data = list(data)
        self._session = session
        self._model = model

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def all(self):
        return list(self._data)

    def first(self):
        return self._data[0] if self._data else None


class FakeSession:
    def __init__(
        self,
        keyword=None,
        keywords=None,
        existing_videos=None,
        existing_comments=None,
    ):
        self.keyword = keyword
        self.keywords = keywords or ([keyword] if keyword else [])
        self.existing_videos = existing_videos or []
        self.existing_comments = existing_comments or []
        self.existing_tasks = []
        self.added = []
        self.committed = False
        self.commit_count = 0
        self.rolled_back = False
        self.closed = False
        self._next_video_id = 100

    def query(self, model):
        if model is Keyword:
            return FakeQuery(self.keywords)
        if model is Video:
            return FakeQuery(self.existing_videos)
        if model is Comment:
            return FakeQuery(self.existing_comments)
        if model is CrawlTask:
            return FakeQuery(self.existing_tasks)
        raise AssertionError(f"Unexpected model: {model}")

    def add(self, obj):
        if obj not in self.added:
            self.added.append(obj)
        if isinstance(obj, Video) and obj.id is None:
            obj.id = self._next_video_id
            self._next_video_id += 1

    def flush(self):
        for obj in self.added:
            if isinstance(obj, Video) and obj.id is None:
                obj.id = self._next_video_id
                self._next_video_id += 1

    def commit(self):
        self.committed = True
        self.commit_count += 1

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class FakeDouyinClient:
    def __init__(self, videos=None, comments=None, comment_errors=None):
        self._videos = videos or []
        self._comments = comments or []
        self._comment_errors = comment_errors or {}
        self.search_calls = []
        self.comment_calls = []

    async def search_videos(self, keyword, time_window="30d", limit=100, min_heat=1000):
        self.search_calls.append(
            {
                "keyword": keyword,
                "time_window": time_window,
                "limit": limit,
                "min_heat": min_heat,
            }
        )
        return list(self._videos)

    async def get_comments(self, video_id, limit=50, sort_by="like"):
        self.comment_calls.append(
            {"video_id": video_id, "limit": limit, "sort_by": sort_by}
        )
        if video_id in self._comment_errors:
            raise self._comment_errors[video_id]
        return list(self._comments)


@pytest.fixture
def keyword():
    return Keyword(
        id=1,
        keyword="美食",
        category_id=1,
        status="active",
        crawl_threshold=1000,
        priority=5,
    )


@pytest.fixture
def sample_videos():
    now = datetime.now(timezone.utc)
    return [
        {
            "external_id": "v_001",
            "title": "美食视频 1",
            "author_name": "厨师 A",
            "author_id": "a_001",
            "cover_url": "https://p/1.jpg",
            "video_url": "https://v/1.mp4",
            "like_count": 5000,
            "comment_count": 300,
            "share_count": 100,
            "publish_time": (now - timedelta(hours=3)).isoformat(),
        },
        {
            "external_id": "v_002",
            "title": "美食视频 2",
            "author_name": "厨师 B",
            "author_id": "a_002",
            "cover_url": "https://p/2.jpg",
            "video_url": "https://v/2.mp4",
            "like_count": 2000,
            "comment_count": 100,
            "share_count": 50,
            "publish_time": (now - timedelta(hours=5)).isoformat(),
        },
    ]


@pytest.fixture
def sample_comments():
    now = datetime.now(timezone.utc)
    return [
        {
            "external_comment_id": "c_001",
            "author_name": "用户 1",
            "content": "太香了",
            "like_count": 88,
            "publish_time": (now - timedelta(hours=1)).isoformat(),
        },
        {
            "external_comment_id": "c_002",
            "author_name": "用户 2",
            "content": "学到了",
            "like_count": 55,
            "publish_time": (now - timedelta(hours=2)).isoformat(),
        },
    ]


def test_crawl_keyword_task_success(
    monkeypatch, keyword, sample_videos, sample_comments
):
    session = FakeSession(keyword=keyword)
    client = FakeDouyinClient(videos=sample_videos, comments=sample_comments)
    processor_calls: list[int] = []

    monkeypatch.setattr(crawler, "SessionLocal", lambda: session)
    monkeypatch.setattr(crawler, "_get_client_for_platform", lambda platform: client)
    monkeypatch.setattr(crawler.settings, "AUTO_GENERATE_SUMMARY_AFTER_CRAWL", False)
    monkeypatch.setattr(
        crawler.generate_summary_task, "delay", lambda vid: processor_calls.append(vid)
    )

    result = crawler.crawl_keyword_task.run(1)

    assert result["status"] == "success"
    assert result["keyword_id"] == 1
    assert result["videos_crawled"] == 2

    videos_added = [o for o in session.added if isinstance(o, Video)]
    assert len(videos_added) == 2
    v1 = next(v for v in videos_added if v.external_id == "v_001")
    assert v1.keyword_id == 1
    assert v1.like_count == 5000
    assert v1.heat_score is not None and v1.heat_score > 0

    comments_added = [o for o in session.added if isinstance(o, Comment)]
    assert len(comments_added) == 4  # 2 videos * 2 comments

    tasks_added = [o for o in session.added if isinstance(o, CrawlTask)]
    assert len(tasks_added) == 1
    assert tasks_added[0].status == "success"
    assert tasks_added[0].videos_crawled == 2

    assert session.committed is True
    assert session.closed is True
    assert client.search_calls[0]["keyword"] == "美食"
    assert client.search_calls[0]["min_heat"] == 1000
    assert processor_calls == []


def test_crawl_keyword_task_auto_summary_when_enabled(
    monkeypatch, keyword, sample_videos, sample_comments
):
    session = FakeSession(keyword=keyword)
    client = FakeDouyinClient(videos=sample_videos[:1], comments=sample_comments)
    processor_calls: list[int] = []

    monkeypatch.setattr(crawler, "SessionLocal", lambda: session)
    monkeypatch.setattr(crawler, "_get_client_for_platform", lambda platform: client)
    monkeypatch.setattr(crawler.settings, "AUTO_GENERATE_SUMMARY_AFTER_CRAWL", True)
    monkeypatch.setattr(
        crawler.generate_summary_task, "delay", lambda vid: processor_calls.append(vid)
    )

    result = crawler.crawl_keyword_task.run(1)

    videos_added = [o for o in session.added if isinstance(o, Video)]
    assert result["status"] == "success"
    assert processor_calls == [videos_added[0].id]


def test_crawl_keyword_task_keyword_not_found(monkeypatch):
    session = FakeSession(keyword=None, keywords=[])
    client = FakeDouyinClient()
    monkeypatch.setattr(crawler, "SessionLocal", lambda: session)
    monkeypatch.setattr(crawler, "_get_client_for_platform", lambda platform: client)

    result = crawler.crawl_keyword_task.run(999)

    assert result == {"status": "error", "message": "Keyword 999 not found"}
    assert not any(isinstance(o, Video) for o in session.added)
    assert session.closed is True


def test_crawl_keyword_task_skips_duplicate_videos(
    monkeypatch, keyword, sample_videos, sample_comments
):
    existing = Video(
        id=7, external_id="v_001", keyword_id=1, title="旧标题", like_count=0
    )
    session = FakeSession(keyword=keyword, existing_videos=[existing])
    client = FakeDouyinClient(videos=sample_videos, comments=sample_comments)

    monkeypatch.setattr(crawler, "SessionLocal", lambda: session)
    monkeypatch.setattr(crawler, "_get_client_for_platform", lambda platform: client)

    result = crawler.crawl_keyword_task.run(1)

    added_videos = [o for o in session.added if isinstance(o, Video)]
    assert len(added_videos) == 1
    assert added_videos[0].external_id == "v_002"
    assert result["videos_crawled"] == 1


def test_crawl_keyword_task_skips_duplicate_items_in_same_batch(
    monkeypatch, keyword, sample_videos, sample_comments
):
    duplicated = [sample_videos[0], sample_videos[0], sample_videos[1]]
    session = FakeSession(keyword=keyword)
    client = FakeDouyinClient(videos=duplicated, comments=sample_comments)

    monkeypatch.setattr(crawler, "SessionLocal", lambda: session)
    monkeypatch.setattr(crawler, "_get_client_for_platform", lambda platform: client)

    result = crawler.crawl_keyword_task.run(1)

    added_videos = [o for o in session.added if isinstance(o, Video)]
    assert [v.external_id for v in added_videos] == ["v_001", "v_002"]
    assert result["videos_crawled"] == 2


def test_crawl_keyword_task_strips_nul_characters(
    monkeypatch, keyword, sample_videos, sample_comments
):
    videos = [
        {
            **sample_videos[0],
            "title": "Steam\x00 新游",
            "author_name": "作者\x00",
            "tags": ["游戏\x00", "steam"],
        }
    ]
    comments = [{**sample_comments[0], "content": "评论\x00内容"}]
    session = FakeSession(keyword=keyword)
    client = FakeDouyinClient(videos=videos, comments=comments)

    monkeypatch.setattr(crawler, "SessionLocal", lambda: session)
    monkeypatch.setattr(crawler, "_get_client_for_platform", lambda platform: client)
    monkeypatch.setattr(crawler.settings, "AUTO_GENERATE_SUMMARY_AFTER_CRAWL", False)

    result = crawler.crawl_keyword_task.run(1)

    added_video = next(o for o in session.added if isinstance(o, Video))
    added_comment = next(o for o in session.added if isinstance(o, Comment))
    assert result["status"] == "success"
    assert "\x00" not in added_video.title
    assert "\x00" not in (added_video.author_name or "")
    assert "\x00" not in (added_video.tags or "")
    assert "\x00" not in added_comment.content


def test_crawl_keyword_task_marks_existing_task_running_before_crawl(
    monkeypatch, keyword, sample_videos, sample_comments
):
    task_record = CrawlTask(
        id=251,
        keyword_id=keyword.id,
        task_type="crawl",
        status="pending",
    )
    session = FakeSession(keyword=keyword)
    session.existing_tasks = [task_record]
    client = FakeDouyinClient(videos=sample_videos[:1], comments=sample_comments)
    commit_states: list[str] = []

    original_commit = session.commit

    def track_commit():
        commit_states.append(task_record.status)
        original_commit()

    session.commit = track_commit

    monkeypatch.setattr(crawler, "SessionLocal", lambda: session)
    monkeypatch.setattr(crawler, "_get_client_for_platform", lambda platform: client)
    monkeypatch.setattr(crawler.settings, "AUTO_GENERATE_SUMMARY_AFTER_CRAWL", False)

    result = crawler.crawl_keyword_task.run(1, task_id=251)

    assert result["status"] == "success"
    assert commit_states[0] == "running"
    assert commit_states[-1] == "success"


def test_crawl_keyword_task_skips_failed_video_comments(
    monkeypatch, keyword, sample_videos, sample_comments
):
    session = FakeSession(keyword=keyword)
    client = FakeDouyinClient(
        videos=sample_videos,
        comments=sample_comments,
        comment_errors={"v_001": RuntimeError("comment connect failed")},
    )

    monkeypatch.setattr(crawler, "SessionLocal", lambda: session)
    monkeypatch.setattr(crawler, "_get_client_for_platform", lambda platform: client)
    monkeypatch.setattr(crawler.settings, "AUTO_GENERATE_SUMMARY_AFTER_CRAWL", False)

    result = crawler.crawl_keyword_task.run(1)

    videos_added = [o for o in session.added if isinstance(o, Video)]
    comments_added = [o for o in session.added if isinstance(o, Comment)]
    task_record = next(o for o in session.added if isinstance(o, CrawlTask))
    assert result["status"] == "success"
    assert len(videos_added) == 2
    assert len(comments_added) == 2
    assert task_record.status == "success"
    assert task_record.videos_crawled == 2


def test_crawl_keyword_task_clears_stale_error_on_success(
    monkeypatch, keyword, sample_videos, sample_comments
):
    task_record = CrawlTask(
        id=241,
        keyword_id=keyword.id,
        task_type="crawl",
        status="failed",
        videos_crawled=0,
        error_message="旧错误",
    )
    session = FakeSession(keyword=keyword)
    session.existing_tasks = [task_record]
    client = FakeDouyinClient(videos=sample_videos[:1], comments=sample_comments)

    monkeypatch.setattr(crawler, "SessionLocal", lambda: session)
    monkeypatch.setattr(crawler, "_get_client_for_platform", lambda platform: client)

    result = crawler.crawl_keyword_task.run(1, task_id=241)

    assert result["status"] == "success"
    assert task_record.status == "success"
    assert task_record.error_message is None


def test_crawl_keyword_task_inactive_keyword(monkeypatch):
    keyword = Keyword(
        id=2,
        keyword="停用",
        category_id=1,
        status="disabled",
        crawl_threshold=1000,
        priority=5,
    )
    session = FakeSession(keyword=keyword)
    client = FakeDouyinClient(videos=[{"external_id": "ignored"}])
    monkeypatch.setattr(crawler, "SessionLocal", lambda: session)
    monkeypatch.setattr(crawler, "_get_client_for_platform", lambda platform: client)

    result = crawler.crawl_keyword_task.run(2)

    assert result == {"status": "skipped", "reason": "keyword disabled"}
    assert client.search_calls == []
    assert not any(isinstance(o, Video) for o in session.added)


def test_crawl_video_comments_does_not_auto_summary_when_disabled(
    monkeypatch, sample_comments
):
    video = Video(
        id=9,
        platform="douyin",
        external_id="v_009",
        keyword_id=1,
        title="测试视频",
    )
    session = FakeSession(existing_videos=[video])
    client = FakeDouyinClient(comments=sample_comments)
    processor_calls: list[int] = []

    monkeypatch.setattr(crawler, "SessionLocal", lambda: session)
    monkeypatch.setattr(crawler, "_get_client_for_platform", lambda platform: client)
    monkeypatch.setattr(crawler.settings, "AUTO_GENERATE_SUMMARY_AFTER_CRAWL", False)
    monkeypatch.setattr(
        crawler.generate_summary_task, "delay", lambda vid: processor_calls.append(vid)
    )

    result = crawler.crawl_video_comments.run(9)

    assert result["status"] == "success"
    assert result["new_comments"] == 2
    assert processor_calls == []


def test_cleanup_browser_locks_supports_bili_alias(monkeypatch, tmp_path):
    user_data_dir = tmp_path / "bili_user_data_dir"
    user_data_dir.mkdir()
    for name in crawler._LOCK_FILES:
        (user_data_dir / name).write_text("locked", encoding="utf-8")

    monkeypatch.setitem(crawler._BROWSER_DATA_DIRS, "bili", user_data_dir)

    calls = []
    monkeypatch.setattr(
        crawler.subprocess,
        "run",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    crawler.cleanup_browser_locks("bili")

    for name in crawler._LOCK_FILES:
        assert not (user_data_dir / name).exists()
    assert calls


def test_crawl_all_keywords_dispatches(monkeypatch):
    active = [
        Keyword(id=1, keyword="a", category_id=1, status="active", priority=8, crawl_threshold=1000),
        Keyword(id=2, keyword="b", category_id=1, status="active", priority=3, crawl_threshold=1000),
    ]
    session = FakeSession(keywords=active)
    monkeypatch.setattr(crawler, "SessionLocal", lambda: session)
    dispatched: list[int] = []
    monkeypatch.setattr(
        crawler.crawl_keyword_task, "delay", lambda kid, platform="douyin": dispatched.append(kid)
    )

    result = crawler.crawl_all_keywords.run()

    assert result == {"status": "success", "dispatched": 2}
    assert dispatched == [1, 2]
    assert session.closed is True


def test_crawl_keyword_task_queue_configuration():
    assert crawler.crawl_keyword_task.name == "app.tasks.crawler.crawl_keyword"
    assert crawler.crawl_keyword_task.queue == "crawler"
    assert crawler.crawl_all_keywords.name == "app.tasks.crawler.crawl_all_keywords"
    assert crawler.crawl_all_keywords.queue == "crawler"
