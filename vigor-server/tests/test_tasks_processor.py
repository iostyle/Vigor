import json
import pytest

from app.models.comment import Comment, CommentSummary
from app.models.video import Video
from app.tasks import processor


class FakeQuery:
    def __init__(self, data):
        self._data = data

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def first(self):
        return self._data[0] if self._data else None

    def all(self):
        return list(self._data)


class FakeSession:
    def __init__(self, video=None, comments=None, summary=None):
        self.video = video
        self.comments = comments or []
        self.summary = summary
        self.committed = False
        self.rolled_back = False
        self.closed = False
        self.added = None

    def query(self, model):
        if model is Video:
            return FakeQuery([self.video] if self.video else [])
        if model is Comment:
            return FakeQuery(self.comments)
        if model is CommentSummary:
            return FakeQuery([self.summary] if self.summary else [])
        raise AssertionError(f"Unexpected model: {model}")

    def add(self, obj):
        self.added = obj

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class FakeDoubaoClient:
    async def generate_video_summary(self, title):
        return f"摘要: {title}"

    async def generate_comment_summary(self, comments):
        return {
            "summary": f"评论数: {len(comments)}",
            "sentiment": "positive",
            "top_keywords": ["好看", "喜欢"],
        }


@pytest.fixture
def video():
    return Video(id=1, title="测试视频标题", summary=None)


@pytest.fixture
def comments():
    return [
        Comment(content="太好看了", like_count=10),
        Comment(content="很喜欢", like_count=8),
    ]


def test_generate_summary_task_success(monkeypatch, video, comments):
    session = FakeSession(video=video, comments=comments)
    monkeypatch.setattr(processor, "SessionLocal", lambda: session)
    monkeypatch.setattr(processor, "_get_doubao_client", lambda: FakeDoubaoClient())

    result = processor.generate_summary_task.run(1)

    assert result == {"status": "success", "video_id": 1}
    assert video.summary == "摘要: 测试视频标题"
    assert video.summary_generated_at is not None
    assert session.committed is True
    assert session.closed is True
    assert session.added is not None
    assert session.added.video_id == 1
    assert session.added.summary == "评论数: 2"
    assert session.added.sentiment == "positive"
    assert json.loads(session.added.top_keywords) == ["好看", "喜欢"]
    assert session.added.comment_count == 2


def test_generate_summary_task_updates_existing_summary(monkeypatch, video, comments):
    existing = CommentSummary(video_id=1, summary="旧摘要", sentiment="neutral", top_keywords='["旧"]', comment_count=1)
    session = FakeSession(video=video, comments=comments, summary=existing)
    monkeypatch.setattr(processor, "SessionLocal", lambda: session)
    monkeypatch.setattr(processor, "_get_doubao_client", lambda: FakeDoubaoClient())

    result = processor.generate_summary_task.run(1)

    assert result == {"status": "success", "video_id": 1}
    assert session.added is None
    assert existing.summary == "评论数: 2"
    assert existing.sentiment == "positive"
    assert json.loads(existing.top_keywords) == ["好看", "喜欢"]
    assert existing.comment_count == 2


def test_generate_summary_task_video_not_found(monkeypatch):
    session = FakeSession(video=None)
    monkeypatch.setattr(processor, "SessionLocal", lambda: session)
    monkeypatch.setattr(processor, "_get_doubao_client", lambda: FakeDoubaoClient())

    result = processor.generate_summary_task.run(999)

    assert result == {"status": "error", "message": "Video 999 not found"}
    assert session.committed is False
    assert session.closed is True


def test_generate_summary_task_queue_configuration():
    assert processor.generate_summary_task.name == "app.tasks.processor.generate_summary"
    assert processor.generate_summary_task.queue == "processor"
    assert processor.generate_summary_task.max_retries == 5
    assert processor.generate_summary_task.default_retry_delay == 30
