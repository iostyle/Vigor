"""BilibiliClient 基础测试

验证 mock 模式的字段兼容性、Protocol 满足度、归一化静态方法。
真实 MediaCrawler 子进程链路在此不测,留给 scripts/test_real_crawler.py。
"""
import pytest

from app.services.bilibili_client import BilibiliClient
from app.services.platform_client import PlatformClient


@pytest.fixture
def client():
    return BilibiliClient(mock_mode=True)


def test_satisfies_platform_protocol(client):
    assert isinstance(client, PlatformClient)


@pytest.mark.asyncio
async def test_search_videos_returns_list(client):
    videos = await client.search_videos("数码", limit=8, min_heat=0)
    assert isinstance(videos, list)
    assert len(videos) > 0
    assert len(videos) <= 8


@pytest.mark.asyncio
async def test_search_videos_item_structure(client):
    videos = await client.search_videos("科技", limit=3, min_heat=0)
    expected_keys = {
        "douyin_id",
        "title",
        "author_name",
        "author_id",
        "cover_url",
        "video_url",
        "like_count",
        "comment_count",
        "share_count",
        "publish_time",
    }
    for item in videos:
        assert expected_keys.issubset(item.keys())
        assert isinstance(item["like_count"], int)
        assert isinstance(item["comment_count"], int)
        assert isinstance(item["share_count"], int)


@pytest.mark.asyncio
async def test_search_videos_with_comments(client):
    videos = await client.search_videos(
        "游戏", limit=2, min_heat=0, include_comments=True, comments_per_video=3
    )
    assert videos
    for v in videos:
        assert "comments" in v
        assert len(v["comments"]) == 3
        for c in v["comments"]:
            assert {"douyin_comment_id", "author_name", "content", "like_count", "publish_time"}.issubset(c.keys())


@pytest.mark.asyncio
async def test_get_comments_mock(client):
    comments = await client.get_comments("av999", limit=5, sort_by="like")
    assert len(comments) == 5
    likes = [c["like_count"] for c in comments]
    assert likes == sorted(likes, reverse=True)


@pytest.mark.asyncio
async def test_get_video_detail_mock(client):
    detail = await client.get_video_detail("av999")
    assert detail["douyin_id"] == "av999"
    assert "title" in detail


def test_normalize_bili_item_maps_fields():
    raw = {
        "video_id": "av123",
        "title": "标题",
        "nickname": "up主",
        "user_id": "42",
        "liked_count": "1000",
        "video_comment": "50",
        "video_share_count": "20",
        "video_cover_url": "c.jpg",
        "video_url": "",
        "create_time": 1_700_000_000,
    }
    norm = BilibiliClient._normalize_bili_item(raw)
    assert norm["douyin_id"] == "av123"
    assert norm["like_count"] == 1000
    assert norm["comment_count"] == 50
    assert norm["share_count"] == 20
    assert norm["author_id"] == "42"
    assert norm["video_url"].startswith("https://www.bilibili.com/video/")


def test_normalize_bili_comment_handles_string_content():
    raw = {
        "video_id": "av123",
        "comment_id": "r1",
        "content": "纯文本评论",
        "nickname": "u1",
        "like_count": "3,456",
        "create_time": 1_700_000_001,
    }
    norm = BilibiliClient._normalize_bili_comment(raw)
    assert norm["douyin_comment_id"] == "r1"
    assert norm["content"] == "纯文本评论"
    assert norm["like_count"] == 3456


def test_normalize_bili_comment_handles_dict_content():
    raw = {
        "video_id": "av123",
        "comment_id": "r2",
        "content": {"message": "嵌套评论"},
        "nickname": "u2",
        "like_count": 7,
    }
    norm = BilibiliClient._normalize_bili_comment(raw)
    assert norm["content"] == "嵌套评论"
