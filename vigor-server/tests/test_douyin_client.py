import pytest

from app.services.douyin_client import DouyinClient


@pytest.fixture
def client():
    return DouyinClient(api_key="test_key", mock_mode=True)


@pytest.mark.asyncio
async def test_search_videos_returns_list(client):
    videos = await client.search_videos("美食", limit=10)
    assert isinstance(videos, list)
    assert len(videos) > 0
    assert len(videos) <= 10


@pytest.mark.asyncio
async def test_search_videos_item_structure(client):
    videos = await client.search_videos("科技", limit=3)
    expected_keys = {
        "external_id",
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
        assert isinstance(item["external_id"], str)
        assert isinstance(item["like_count"], int)
        assert isinstance(item["comment_count"], int)
        assert isinstance(item["share_count"], int)


@pytest.mark.asyncio
async def test_search_videos_respects_min_heat(client):
    videos = await client.search_videos("美食", limit=50, min_heat=5000)
    for item in videos:
        heat = item["like_count"] + item["comment_count"] * 3 + item["share_count"] * 5
        assert heat >= 5000


@pytest.mark.asyncio
async def test_get_video_detail_structure(client):
    detail = await client.get_video_detail("mock_video_001")
    assert isinstance(detail, dict)
    assert detail["external_id"] == "mock_video_001"
    for key in (
        "title",
        "author_name",
        "like_count",
        "comment_count",
        "share_count",
    ):
        assert key in detail


@pytest.mark.asyncio
async def test_get_comments_returns_list(client):
    comments = await client.get_comments("mock_video_001", limit=20)
    assert isinstance(comments, list)
    assert len(comments) > 0
    assert len(comments) <= 20


@pytest.mark.asyncio
async def test_get_comments_item_structure(client):
    comments = await client.get_comments("mock_video_001", limit=5)
    expected_keys = {
        "external_comment_id",
        "author_name",
        "content",
        "like_count",
        "publish_time",
    }
    for item in comments:
        assert expected_keys.issubset(item.keys())


@pytest.mark.asyncio
async def test_get_comments_sort_by_like_descending(client):
    comments = await client.get_comments("mock_video_001", limit=30, sort_by="like")
    likes = [c["like_count"] for c in comments]
    assert likes == sorted(likes, reverse=True)


@pytest.mark.asyncio
async def test_real_mode_search_uses_media_crawler(monkeypatch):
    called = {}

    async def fake_search(
        self,
        keyword,
        limit,
        include_comments=False,
        comments_per_video=20,
    ):
        called["keyword"] = keyword
        called["limit"] = limit
        called["include_comments"] = include_comments
        called["comments_per_video"] = comments_per_video
        return [{"external_id": "real_aweme_001"}]

    monkeypatch.setattr(DouyinClient, "_run_media_crawler_search", fake_search)

    real_client = DouyinClient(api_key="test_key", mock_mode=False)
    videos = await real_client.search_videos(
        "美食",
        limit=1,
        include_comments=True,
        comments_per_video=3,
    )

    assert videos == [{"external_id": "real_aweme_001"}]
    assert called == {
        "keyword": "美食",
        "limit": 1,
        "include_comments": True,
        "comments_per_video": 3,
    }


def test_real_mode_builds_media_crawler_env(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "")
    monkeypatch.setenv("HTTPS_PROXY", "")
    client = DouyinClient(
        api_key="test_key",
        mock_mode=False,
        login_type="cookie",
        cookies="LOGIN_STATUS=1",
        enable_cdp=True,
        headless=False,
    )

    env = client._media_crawler_env()

    assert env["VIGOR_MC_LOGIN_TYPE"] == "cookie"
    assert env["VIGOR_MC_COOKIES"] == "LOGIN_STATUS=1"
    assert env["VIGOR_MC_ENABLE_CDP_MODE"] == "true"
    assert env["VIGOR_MC_HEADLESS"] == "false"
