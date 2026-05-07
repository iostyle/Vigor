"""Pydantic schema 字段校验测试"""
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.keyword import KeywordCreate, KeywordUpdate, KeywordResponse
from app.schemas.video import VideoResponse, VideoListResponse
from app.schemas.comment import CommentResponse, CommentSummaryResponse
from app.schemas.task import CrawlTaskResponse


class TestKeywordCreate:
    def test_valid_minimal(self):
        schema = KeywordCreate(keyword="美食")
        assert schema.keyword == "美食"
        assert schema.category is None
        assert schema.crawl_threshold == 1000
        assert schema.priority == 5

    def test_valid_full(self):
        schema = KeywordCreate(
            keyword="科技数码",
            category="科技",
            crawl_threshold=500,
            priority=8,
        )
        assert schema.keyword == "科技数码"
        assert schema.category == "科技"
        assert schema.crawl_threshold == 500
        assert schema.priority == 8

    def test_keyword_required(self):
        with pytest.raises(ValidationError):
            KeywordCreate()

    def test_keyword_empty_string_rejected(self):
        with pytest.raises(ValidationError):
            KeywordCreate(keyword="")

    def test_priority_range(self):
        with pytest.raises(ValidationError):
            KeywordCreate(keyword="test", priority=0)
        with pytest.raises(ValidationError):
            KeywordCreate(keyword="test", priority=11)

    def test_crawl_threshold_positive(self):
        with pytest.raises(ValidationError):
            KeywordCreate(keyword="test", crawl_threshold=-1)


class TestKeywordUpdate:
    def test_all_optional(self):
        schema = KeywordUpdate()
        assert schema.keyword is None
        assert schema.category is None
        assert schema.status is None
        assert schema.crawl_threshold is None
        assert schema.priority is None

    def test_partial_update(self):
        schema = KeywordUpdate(status="paused", priority=3)
        assert schema.status == "paused"
        assert schema.priority == 3
        assert schema.keyword is None

    def test_status_whitelist(self):
        with pytest.raises(ValidationError):
            KeywordUpdate(status="unknown")

    def test_priority_range(self):
        with pytest.raises(ValidationError):
            KeywordUpdate(priority=0)
        with pytest.raises(ValidationError):
            KeywordUpdate(priority=11)


class TestKeywordResponse:
    def test_from_attributes(self):
        class FakeORM:
            id = 1
            keyword = "美食"
            category = "生活"
            status = "active"
            crawl_threshold = 1000
            priority = 5
            created_at = datetime(2026, 5, 7, 10, 0, 0)
            updated_at = datetime(2026, 5, 7, 10, 0, 0)

        schema = KeywordResponse.model_validate(FakeORM())
        assert schema.id == 1
        assert schema.keyword == "美食"
        assert schema.status == "active"


class TestCommentResponse:
    def test_roundtrip(self):
        schema = CommentResponse(
            id=1,
            content="好看",
            author_name="user_1",
            like_count=10,
            publish_time=datetime(2026, 5, 1),
        )
        assert schema.id == 1
        assert schema.content == "好看"


class TestCommentSummaryResponse:
    def test_top_keywords_is_list(self):
        schema = CommentSummaryResponse(
            summary="正面反馈为主",
            top_keywords=["好吃", "赞", "推荐"],
            sentiment="positive",
            generated_at=datetime(2026, 5, 7),
            comment_count=42,
        )
        assert schema.top_keywords == ["好吃", "赞", "推荐"]
        assert schema.sentiment == "positive"

    def test_sentiment_whitelist(self):
        with pytest.raises(ValidationError):
            CommentSummaryResponse(
                summary="",
                top_keywords=[],
                sentiment="angry",
                generated_at=datetime(2026, 5, 7),
                comment_count=0,
            )


class TestVideoResponse:
    def test_minimal(self):
        schema = VideoResponse(
            id=1,
            douyin_id="dy_001",
            title="测试视频",
            author_name="up",
            like_count=100,
            comment_count=20,
            share_count=5,
            heat_score=123.4,
            publish_time=datetime(2026, 5, 1),
            summary="摘要",
            comment_summary=None,
        )
        assert schema.douyin_id == "dy_001"
        assert schema.comment_summary is None

    def test_with_comment_summary(self):
        schema = VideoResponse(
            id=2,
            douyin_id="dy_002",
            title="t",
            author_name="a",
            like_count=0,
            comment_count=0,
            share_count=0,
            heat_score=0.0,
            publish_time=datetime(2026, 5, 1),
            summary=None,
            comment_summary=CommentSummaryResponse(
                summary="正向",
                top_keywords=["好"],
                sentiment="positive",
                generated_at=datetime(2026, 5, 7),
                comment_count=1,
            ),
        )
        assert schema.comment_summary.sentiment == "positive"


class TestVideoListResponse:
    def test_shape(self):
        schema = VideoListResponse(total=0, data=[])
        assert schema.total == 0
        assert schema.data == []

    def test_total_non_negative(self):
        with pytest.raises(ValidationError):
            VideoListResponse(total=-1, data=[])


class TestCrawlTaskResponse:
    def test_minimal(self):
        schema = CrawlTaskResponse(
            id=1,
            keyword_id=1,
            task_type="crawl",
            status="success",
            videos_crawled=42,
            error_message=None,
            started_at=datetime(2026, 5, 7),
            completed_at=datetime(2026, 5, 7),
        )
        assert schema.status == "success"

    def test_status_whitelist(self):
        with pytest.raises(ValidationError):
            CrawlTaskResponse(
                id=1,
                keyword_id=1,
                task_type="crawl",
                status="exploded",
                videos_crawled=0,
                error_message=None,
                started_at=None,
                completed_at=None,
            )
