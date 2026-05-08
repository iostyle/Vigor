from app.models.keyword import Keyword
from app.models.video import Video
from app.models.comment import Comment, CommentSummary
from app.models.task import CrawlTask
from app.database import Base


def test_keyword_model_structure():
    """测试 Keyword 模型的结构和字段定义"""
    # 验证表名
    assert Keyword.__tablename__ == "keywords"

    # 验证字段存在
    columns = Keyword.__table__.columns
    assert "id" in columns
    assert "keyword" in columns
    assert "category" in columns
    assert "status" in columns
    assert "crawl_threshold" in columns
    assert "priority" in columns
    assert "created_at" in columns
    assert "updated_at" in columns

    # 验证主键
    assert columns["id"].primary_key is True

    # 验证 nullable 约束
    assert columns["keyword"].nullable is False

    # 验证默认值
    assert columns["status"].default.arg == "active"
    assert columns["crawl_threshold"].default.arg == 1000
    assert columns["priority"].default.arg == 5


def test_keyword_model_instantiation():
    """测试 Keyword 模型的实例化"""
    keyword = Keyword(
        keyword="美食",
        category="生活",
        status="active",
        crawl_threshold=1000,
        priority=5
    )

    assert keyword.keyword == "美食"
    assert keyword.category == "生活"
    assert keyword.status == "active"
    assert keyword.crawl_threshold == 1000
    assert keyword.priority == 5


def test_video_model_structure():
    """测试 Video 模型的结构和字段定义"""
    assert Video.__tablename__ == "videos"

    columns = Video.__table__.columns
    assert "id" in columns
    assert "external_id" in columns
    assert "keyword_id" in columns
    assert "title" in columns
    assert "author_name" in columns
    assert "like_count" in columns
    assert "comment_count" in columns
    assert "share_count" in columns
    assert "heat_score" in columns
    assert "summary" in columns

    # 验证主键和唯一约束
    assert columns["id"].primary_key is True
    assert columns["external_id"].unique is True
    assert columns["external_id"].nullable is False
    assert columns["title"].nullable is False


def test_comment_model_structure():
    """测试 Comment 模型的结构和字段定义"""
    assert Comment.__tablename__ == "comments"

    columns = Comment.__table__.columns
    assert "id" in columns
    assert "video_id" in columns
    assert "external_comment_id" in columns
    assert "author_name" in columns
    assert "content" in columns
    assert "like_count" in columns

    assert columns["id"].primary_key is True
    assert columns["content"].nullable is False


def test_comment_summary_model_structure():
    """测试 CommentSummary 模型的结构和字段定义"""
    assert CommentSummary.__tablename__ == "comment_summaries"

    columns = CommentSummary.__table__.columns
    assert "id" in columns
    assert "video_id" in columns
    assert "summary" in columns
    assert "top_keywords" in columns
    assert "sentiment" in columns
    assert "comment_count" in columns

    assert columns["id"].primary_key is True
    assert columns["video_id"].unique is True


def test_crawl_task_model_structure():
    """测试 CrawlTask 模型的结构和字段定义"""
    assert CrawlTask.__tablename__ == "crawl_tasks"

    columns = CrawlTask.__table__.columns
    assert "id" in columns
    assert "keyword_id" in columns
    assert "task_type" in columns
    assert "status" in columns
    assert "videos_crawled" in columns
    assert "error_message" in columns

    assert columns["id"].primary_key is True
    assert columns["videos_crawled"].default.arg == 0
