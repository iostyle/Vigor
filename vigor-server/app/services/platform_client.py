"""平台 client 抽象契约 + 工厂

各平台 client 的返回字典约定(统一字段):
- 视频: external_id, title, author_name, author_id, cover_url, video_url,
        like_count, comment_count, share_count, publish_time
- 评论: external_comment_id, author_name, content, like_count, publish_time

工厂部分根据显式传入的 platform 参数分发到具体 client 实现。
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from app.config import settings
from app.services.douyin_client import DouyinClient


@runtime_checkable
class PlatformClient(Protocol):
    """平台数据接口最小契约

    所有具体 client(DouyinClient / BilibiliClient / ...)都应满足此 Protocol。
    使用 `runtime_checkable` 可在测试中用 `isinstance(client, PlatformClient)` 做冒烟。
    """

    mock_mode: bool

    async def search_videos(
        self,
        keyword: str,
        time_window: str = "30d",
        limit: int = 100,
        min_heat: int = 1000,
        include_comments: bool = False,
        comments_per_video: int = 20,
    ) -> list[dict]:
        """按关键词搜索视频,返回归一化后的视频列表"""
        ...

    async def get_comments(
        self,
        video_id: str,
        limit: int = 50,
        sort_by: str = "like",
    ) -> list[dict]:
        """按视频 id 抓评论,返回归一化后的评论列表"""
        ...

    async def get_video_detail(self, video_id: str) -> dict:
        """取单个视频详情"""
        ...


def _build_douyin_client() -> PlatformClient:
    return DouyinClient(
        api_key=settings.DOUYIN_API_KEY,
        mock_mode=settings.DOUYIN_MOCK_MODE,
        base_url=settings.DOUYIN_API_BASE_URL,
        max_concurrency=settings.DOUYIN_MAX_CONCURRENCY,
        login_type=settings.DOUYIN_LOGIN_TYPE,
        cookies=settings.DOUYIN_COOKIES,
        enable_cdp=settings.DOUYIN_ENABLE_CDP_MODE,
        headless=settings.DOUYIN_HEADLESS,
    )


def _build_bilibili_client() -> PlatformClient:
    # Why: 延迟 import 避免在 DouyinClient 老链路里引入新依赖
    from app.services.bilibili_client import BilibiliClient

    return BilibiliClient(
        mock_mode=settings.BILIBILI_MOCK_MODE,
        max_concurrency=settings.BILIBILI_MAX_CONCURRENCY,
    )


# 平台别名到工厂的映射,后续新增平台只加一行
_PLATFORM_FACTORIES: dict[str, Any] = {
    "douyin": _build_douyin_client,
    "dy": _build_douyin_client,
    "bilibili": _build_bilibili_client,
    "bili": _build_bilibili_client,
}


def get_client(platform: str | None) -> PlatformClient:
    """根据平台名返回对应的 client 实例

    platform 为 None 或空字符串时按 'douyin' 处理,保持向后兼容。
    未知 platform 抛 ValueError,方便在任务层 catch 后落库为 failed。
    """
    key = (platform or "douyin").lower()
    factory = _PLATFORM_FACTORIES.get(key)
    if factory is None:
        raise ValueError(f"不支持的 platform: {platform}")
    return factory()
